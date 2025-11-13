from typing import Dict, Tuple

import pandas as pd


class StrategyTables:
    """Loads and caches strategy tables"""

    def __init__(self, strategy_sheet_path: str):
        self.split_cache: Dict[Tuple[str, str], bool] = {}
        self.surrender_cache: Dict[Tuple[str, str], bool] = {}
        self.soft_cache: Dict[Tuple[str, str], str] = {}
        self.hard_cache: Dict[Tuple[str, str], str] = {}
        self._load_tables(strategy_sheet_path)

    def _load_tables(self, path: str):
        """Load all strategy tables from Excel"""
        print("Loading strategy tables...")

        split_df = pd.read_excel(path, sheet_name="Split")
        split_df.columns = split_df.columns.map(str)
        split_df[split_df.columns[0]] = split_df[split_df.columns[0]].astype("string")
        split_df.set_index(split_df.columns[0], inplace=True)

        surrender_df = pd.read_excel(path, sheet_name="Surrender")
        surrender_df.columns = surrender_df.columns.map(str)
        surrender_df[surrender_df.columns[0]] = surrender_df[
            surrender_df.columns[0]
        ].astype("string")
        surrender_df.set_index(surrender_df.columns[0], inplace=True)

        soft_df = pd.read_excel(path, sheet_name="Soft Totals")
        soft_df.columns = soft_df.columns.map(str)
        soft_df[soft_df.columns[0]] = soft_df[soft_df.columns[0]].astype(str)
        soft_df.set_index(soft_df.columns[0], inplace=True)

        hard_df = pd.read_excel(path, sheet_name="Hard Totals")
        hard_df.columns = hard_df.columns.map(str)
        hard_df[hard_df.columns[0]] = hard_df[hard_df.columns[0]].astype(str)
        hard_df.set_index(hard_df.columns[0], inplace=True)

        print("Building strategy lookup cache...")

        for player in split_df.index:
            for dealer_col in split_df.columns:
                self.split_cache[(player, dealer_col)] = split_df.loc[
                    player, dealer_col
                ]

        for player in surrender_df.index:
            for dealer_col in surrender_df.columns:
                self.surrender_cache[(player, dealer_col)] = surrender_df.loc[
                    player, dealer_col
                ]

        for player in soft_df.index:
            for dealer_col in soft_df.columns:
                self.soft_cache[(player, dealer_col)] = soft_df.loc[player, dealer_col]

        for player in hard_df.index:
            for dealer_col in hard_df.columns:
                self.hard_cache[(player, dealer_col)] = hard_df.loc[player, dealer_col]

        print("Strategy cache built!")
