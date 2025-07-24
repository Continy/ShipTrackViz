import xarray
import json
import numpy as np
import pandas as pd
from yacs.config import CfgNode as CN
from pathlib import Path
import os
import yaml
import shutil
# Sheet header indentifier using LLM
from google import genai
from google.genai import types


def build_cfg(yaml_path):

    with open(yaml_path, 'r') as f:
        cfg = CN(yaml.safe_load(f))

    return cfg


class DataExtractor:
    """
    A class to extract and process basic information from data files (CSV, XLSX)
    using Pandas and a large language model.
    """

    def __init__(self, path: str, cfg: CN, force_regeneration: bool = False):
        """
        Initializes the DataExtractor.

        Args:
            llm_client: An instance of the language model client.
            llm_model (str): The model identifier to be used for generation.
            prompt_yaml_path (str): The file path to the YAML configuration for prompts.
        """
        self.path = str(Path(path).resolve())
        self.client = genai.Client()
        self.cfg = cfg
        self.model = self.cfg.model
        self.encode = self.cfg.encode
        self.filetype = None
        '''Initialization'''
        # cache directory

        self.cache_path = self._cache_path(path)
        if force_regeneration and os.path.exists(self.cache_path):
            print(
                f"Force regeneration: Deleting old cache at {self.cache_path}")
            # Handle both files and directories safely
            if os.path.isdir(self.cache_path):
                shutil.rmtree(self.cache_path
                              )  # Safely removes directory and all contents
            else:
                os.remove(self.cache_path)  # It's a file, just remove it

        # 2. Ensure the cache directory exists for use.
        # This will create it if it doesn't exist, or do nothing if it already does.
        os.makedirs(self.cache_path, exist_ok=True)
        # open yaml file to save the configuration
        self.cfg_path = os.path.join(self.cache_path, 'config.yaml')
        if not os.path.exists(self.cfg_path):
            # If the config file does not exist, create it
            with open(self.cfg_path, 'w') as f:
                self.cfg.filetype = self._get_suffix(path)
                self.cfg.header = self.get_header_as_json(path)
                self.cfg.deltatime = self.get_delta_time(self.cfg.header)
                self.cfg.ranges = self.get_range(self.cfg.header)
                f.write(self.cfg.dump())
        else:
            # If the config file exists, load it
            with open(self.cfg_path, 'r') as f:
                self.cfg = CN(yaml.safe_load(f))

    def __str__(self):
        return f"DataExtractor(path={self.path}, model={self.model}, encode={self.encode})"

    @staticmethod
    def _cache_path(path: str) -> str:
        """Returns the cache path for the given file path."""
        original_path = Path(path)
        filename = original_path.stem
        parent_dir = original_path.parent
        cache_dir = parent_dir / filename
        return str(cache_dir)

    @staticmethod
    def _build_cfg(yaml_path: str) -> CN:
        """Loads configuration from a YAML file."""
        return build_cfg(yaml_path)

    @staticmethod
    def read_txt(filepath: str, encoding: str = 'utf-8') -> str:

        with open(filepath, 'r', encoding=encoding) as file:
            content = file.read()
        return content

    @staticmethod
    def _get_suffix(path: str) -> str:
        """Gets the file extension from a path."""
        return path.split('.')[-1]

    def load_method(self,
                    file_path: str,
                    suffix: str,
                    encoding: str = 'utf-8',
                    **kwargs) -> pd.DataFrame:
        """Returns the appropriate pandas function to read a file based on its suffix."""
        if suffix == 'csv':
            self.filetype = 'csv'
            return pd.read_csv(file_path, encoding=encoding, **kwargs)
        elif suffix == 'xlsx':
            self.filetype = 'xlsx'
            return pd.read_excel(file_path, **kwargs)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

    def get_header_list(self, file_path: str) -> list:
        """Reads only the header of a data file and returns it as a list."""
        suffix = self._get_suffix(file_path)
        df = self.load_method(file_path,
                              suffix=suffix,
                              encoding=self.encode,
                              nrows=0)
        return df.columns.tolist()

    def get_header_as_json(self, file_path: str) -> CN:
        """
        Sends the file header to an LLM to get a structured JSON representation.
        """
        header_list = self.get_header_list(file_path)
        header_str = str(header_list)
        prompt_template = self.read_txt(self.cfg.header_getter)
        context = f"{header_str}<<{prompt_template}>>"

        # Assuming your client has a 'generate_text' method like the one provided
        response = self.client.models.generate_content(
            model=self.model,
            contents=context,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0),
                temperature=0.1,
            ))
        header = CN()
        header.update(dict(json.loads(response.text)))

        return header

    def get_delta_time(self, header_json: CN) -> float:
        """
        Calculates the time difference in seconds from data within the header JSON.
        Note: This assumes 'header_json' contains rows of data with timestamps.
        """

        timestamp_index = header_json.timestamp
        df_time_column = self.load_method(
            self.path,
            suffix=self.filetype,
            encoding=self.encode,
            usecols=[timestamp_index],
        )
        if df_time_column.empty:
            raise ValueError("Timestamp column is empty")
        # Convert the timestamp column to datetime
        df_time_column = pd.to_datetime(df_time_column.iloc[:, 0],
                                        errors='coerce')
        if df_time_column.isnull().all():
            raise ValueError("All timestamps are invalid or missing")
        # Calculate the time difference in seconds
        time_diff = df_time_column[1] - df_time_column[0]
        if pd.isna(time_diff):
            raise ValueError("Time difference calculation resulted in NaN")
        return time_diff.total_seconds() if time_diff else None

    def get_range(self, header_json: CN) -> CN:
        """
        Extracts the range of values for each column specified in the header JSON.
        """
        range_CN = CN()
        for key in header_json.keys():
            index = header_json[key]
            if index is None:
                continue

            df = self.load_method(
                self.path,
                suffix=self.filetype,
                encoding=self.encode,
                usecols=[index],
            )
            if df.empty:
                raise ValueError(f"Column {key} is empty")
            if key == 'timestamp':
                df = pd.to_datetime(df.iloc[:, 0], errors='coerce')
                range_CN[key] = CN()
                range_CN[key].min = str(df.min().to_pydatetime())
                range_CN[key].max = str(df.max().to_pydatetime())
                continue
            if key == 'longitude':
                # Devide into [-num, 0] and [0, num], it's hard to get data in [+num, -num] in CDS website,
                # the default range order is from -180 to 180, east to west
                df = pd.to_numeric(df.iloc[:, 0], errors='coerce')

                range_CN[key] = CN()
                range_CN[key].neg = [
                    float(df[df < 0].max()),
                    float(df[df < 0].min())
                ]
                range_CN[key].pos = [
                    float(df[df >= 0].min()),
                    float(df[df >= 0].max())
                ]
                continue
            min_val = df.iloc[:, 0].min()
            max_val = df.iloc[:, 0].max()
            range_CN[key] = CN()
            range_CN[key].min = float(min_val)
            range_CN[key].max = float(max_val)
        return range_CN

    def extract_basic_info(self, file_path: str) -> dict:
        """
        Runs the full pipeline to extract basic information from a data file.

        Args:
            file_path (str): The path to the data file.

        Returns:
            dict: A dictionary containing the extracted information.
        """
        suffix = self._get_suffix(file_path)
        header_list = self.get_header_list(file_path)
        header_json_data = self.get_header_as_json(file_path)

        # The delta_time calculation depends on the LLM's output structure
        try:
            delta_time = self.get_delta_time(header_json_data)
        except (ValueError, KeyError, TypeError):
            # Handle cases where the JSON doesn't match the expected format
            delta_time = None

        return {
            "file_path": file_path,
            "file_type": suffix,
            "header": header_list,
            "structured_header": header_json_data,
            "delta_time_seconds": delta_time,
        }


if __name__ == "__main__":
    # Example usage

    data_llm_cfg_path = "./llm/data.yaml"
    cfg = build_cfg(data_llm_cfg_path)
    cfg.encode = 'utf-8'  # Set the encoding to GBK
    file_path = ["./data/split.csv"]
    for path in file_path:
        print(f"Processing file: {path}")
        # Create an instance of DataExtractor
        extractor = DataExtractor(path, cfg, force_regeneration=True)
