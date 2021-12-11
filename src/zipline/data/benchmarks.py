#
# Copyright 2013 Quantopian, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import pandas as pd

import logbook
from zipline.data import bundles
from zipline.data.data_portal import DataPortal

log = logbook.Logger(__name__)


def get_benchmark_returns_from_file(filelike):
    """
    Get a Series of benchmark returns from a file

    Parameters
    ----------
    filelike : str or file-like object
        Path to the benchmark file.
        expected csv file format:
        date,return
        2020-01-02 00:00:00+00:00,0.01
        2020-01-03 00:00:00+00:00,-0.02

    """
    log.info("Reading benchmark returns from {}", filelike)

    df = pd.read_csv(
        filelike,
        index_col=["date"],
        parse_dates=["date"],
    )
    if not df.index.tz:
        df = df.tz_localize("utc")

    if "return" not in df.columns:
        raise ValueError(
            "The column 'return' not found in the "
            "benchmark file \n"
            "Expected benchmark file format :\n"
            "date, return\n"
            "2020-01-02 00:00:00+00:00,0.01\n"
            "2020-01-03 00:00:00+00:00,-0.02\n"
        )

    return df["return"].sort_index()


def get_benchmark_returns(symbol, bundle_name="quandl-eod"):
    """Use the zipline data portal to return benchmark data
    Parameters
    ----------
    symbol : str
        Benchmark symbol string
    bundle_name : str
        The name of the zipline bundle to look for data in
    calendar_name : str
        The calendar that returns the benchmark prices
    Returns
    -------
    returns :
    """
    bundle_data = bundles.load(bundle_name)
    calendar = bundle_data.equity_daily_bar_reader.trading_calendar

    start_date = pd.Timestamp("1990-01-03", tz="UTC")
    end_date = pd.Timestamp("today", tz="UTC")
    bar_count = calendar.session_distance(start_date, end_date)

    portal = DataPortal(
        bundle_data.asset_finder,
        calendar,
        bundle_data.equity_daily_bar_reader.first_trading_day,
        equity_minute_reader=bundle_data.equity_minute_bar_reader,
        equity_daily_reader=bundle_data.equity_daily_bar_reader,
        adjustment_reader=bundle_data.adjustment_reader,
    )

    prices = portal.get_history_window(
        assets=[portal.asset_finder.lookup_symbol(symbol, end_date)],
        end_dt=end_date,
        bar_count=bar_count,
        frequency="1d",
        data_frequency="daily",
        field="close",
    )
    prices.columns = [symbol]

    #
    # api_key = os.environ.get('IEX_API_KEY')
    # if api_key is None:
    #     raise ValueError(
    #         "Please set your IEX_API_KEY environment variable and retry."
    #     )
    # r = requests.get(
    #     "https://cloud.iexapis.com/stable/stock/{}/chart/5y?token={}".format(symbol, api_key)
    # )
    #
    # if r.status_code != 200:
    #     path = loader.get_data_filepath(loader.get_benchmark_filename(symbol))
    #     df = pd.read_csv(path, names=["date", "return"])
    #     df.index = pd.DatetimeIndex(df["date"], tz="UTC")
    #     return df["return"]
    #
    # data = r.json()
    #
    # df = pd.DataFrame(data)
    #
    # df.index = pd.DatetimeIndex(df["date"])
    # df = df["close"]

    return prices.sort_index().dropna().pct_change(1).iloc[1:]