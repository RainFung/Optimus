import builtins
import re

import dask.dataframe as dd
import numpy as np
from dask.dataframe.core import DataFrame
from dask.distributed import as_completed
from multipledispatch import dispatch

from optimus.engines.base.columns import BaseColumns
from optimus.engines.dask.dask import Dask
from optimus.helpers.check import equal_function
from optimus.helpers.columns import parse_columns, validate_columns_names, check_column_numbers, get_output_cols
from optimus.helpers.converter import format_dict, val_to_list
from optimus.helpers.raiseit import RaiseIt
from optimus.infer import Infer, is_list, is_list_of_tuples, is_one_element, is_int
from optimus.infer import is_list_of_futures
from optimus.profiler.functions import fill_missing_var_types


# Some expression accepts multiple columns at the same time.
# python_set = set

# This implementation works for Dask and dask_cudf

class DaskBaseColumns(BaseColumns):

    @staticmethod
    def mode(columns):
        pass

    @staticmethod
    def abs(columns):
        pass

    def __init__(self, df):
        super(DaskBaseColumns, self).__init__(df)

    @staticmethod
    def get_meta(col_name, spec=None):
        pass

    @staticmethod
    def set_meta(col_name, spec=None, value=None, missing=dict):
        pass

    @staticmethod
    def bucketizer(input_cols, splits, output_cols=None):
        pass

    @staticmethod
    def index_to_string(input_cols=None, output_cols=None, columns=None):
        pass

    @staticmethod
    def string_to_index(input_cols=None, output_cols=None, columns=None):
        pass

    @staticmethod
    def values_to_cols(input_cols):
        pass

    @staticmethod
    def clip(columns, lower_bound, upper_bound):
        pass

    @staticmethod
    def qcut(columns, num_buckets, handle_invalid="skip"):
        pass

    @staticmethod
    def boxplot(columns):
        pass

    @staticmethod
    def correlation(input_cols, method="pearson", output="json"):
        pass

    @staticmethod
    def count_mismatch(columns_mismatch: dict = None):
        pass

    def count(self):
        df = self.df
        return len(df)

    @staticmethod
    def frequency_by_group(columns, n=10, percentage=False, total_rows=None):
        pass

    @staticmethod
    def scatter(columns, buckets=10):
        pass

    @staticmethod
    def cell(column):
        pass

    @staticmethod
    def iqr(columns, more=None, relative_error=None):
        pass

    @staticmethod
    def max_abs_scaler(input_cols, output_cols=None):
        pass

    @staticmethod
    def min_max_scaler(input_cols, output_cols=None):
        pass

    @staticmethod
    def z_score(input_cols, output_cols=None):
        pass

    @staticmethod
    def _math(columns, operator, new_column):
        pass

    @staticmethod
    def select_by_dtypes(data_type):
        pass

    @staticmethod
    def nunique(*args, **kwargs):
        pass

    @staticmethod
    def unique(columns):
        pass

    @staticmethod
    def value_counts(columns):
        pass

    @staticmethod
    def count_uniques(columns, estimate=True):
        pass

    @staticmethod
    def count_zeros(columns):
        pass

    @staticmethod
    def count_na(columns):
        pass

    @staticmethod
    def is_na(input_cols, output_cols=None):
        pass

    @staticmethod
    def impute(input_cols, data_type="continuous", strategy="mean", output_cols=None):
        pass

    @staticmethod
    def replace_regex(input_cols, regex=None, value=None, output_cols=None):
        pass

    @staticmethod
    def years_between(input_cols, date_format=None, output_cols=None):
        pass

    @staticmethod
    def remove_white_spaces(input_cols, output_cols=None):
        pass

    @staticmethod
    def remove_special_chars(input_cols, output_cols=None):
        pass

    @staticmethod
    def remove_accents(input_cols, output_cols=None):
        pass

    @staticmethod
    def remove(columns, search=None, search_by="chars", output_cols=None):
        pass

    @staticmethod
    def reverse(input_cols, output_cols=None):
        pass

    @staticmethod
    def drop(columns=None, regex=None, data_type=None):
        pass

    @staticmethod
    def sort(order="asc", columns=None):
        pass

    @staticmethod
    def keep(columns=None, regex=None):
        pass

    @staticmethod
    def move(column, position, ref_col=None):
        pass

    @staticmethod
    def astype(*args, **kwargs):
        pass

    @staticmethod
    def set(output_col, value=None):
        pass

    @staticmethod
    def apply_by_dtypes(columns, func, func_return_type, args=None, func_type=None, data_type=None):
        pass

    @staticmethod
    def apply_expr(input_cols, func=None, args=None, filter_col_by_dtypes=None, output_cols=None, meta=None):
        pass

    @staticmethod
    def to_timestamp(input_cols, date_format=None, output_cols=None):
        pass

    @staticmethod
    def copy(input_cols, output_cols=None, columns=None):
        pass

    @staticmethod
    def append(dfs) -> DataFrame:
        """

        :param dfs:
        :return:
        """
        # df = dd.concat([self, dfs], axis=1)
        raise NotImplementedError
        # return df

    @staticmethod
    def exec_agg(exprs):
        """
        Execute and aggregation
        :param exprs:
        :return:
        """

        agg_list = Dask.instance.compute(exprs)

        if len(agg_list) > 0:
            agg_results = []
            # Distributed mode return a list of Futures objects, Single mode not.
            # TODO: Maybe use .gather
            if is_list_of_futures(agg_list):
                for future in as_completed(agg_list):
                    agg_results.append(future.result())
            else:
                agg_results = agg_list[0]

            result = {}
            # print("AGG_RESULT", agg_result)
            for agg_element in agg_results:
                agg_col_name, agg_element_result = agg_element
                if agg_col_name not in result:
                    result[agg_col_name] = {}

                result[agg_col_name].update(agg_element_result)

            # Parsing results
            def parse_percentile(value):
                _result = {}

                for (p_value, p_result) in value.iteritems():
                    _result.setdefault(p_value, p_result)
                return _result

            def parse_hist(value):
                x = value["count"]
                y = value["bins"]
                _result = []
                for idx, v in enumerate(y):
                    if idx < len(y) - 1:
                        _result.append({"count": x[idx], "lower": y[idx], "upper": y[idx + 1]})
                return _result

            for columns in result.values():
                for agg_name, agg_results in columns.items():
                    if agg_name == "percentile":
                        agg_parsed = parse_percentile(agg_results)
                    elif agg_name == "hist":
                        agg_parsed = parse_hist(agg_results)
                    # elif agg_name in ["min", "max", "stddev", "mean", "variance"]:
                    #     agg_parsed = parse_single(agg_results)
                    else:
                        agg_parsed = agg_results
                    columns[agg_name] = agg_parsed

        else:
            result = None

        return result

    def create_exprs(self, columns, funcs, *args):
        df = self.df
        # Std, kurtosis, mean, skewness and other agg functions can not process date columns.
        filters = {"object": [df.functions.min],
                   }

        def _filter(_col_name, _func):
            for data_type, func_filter in filters.items():
                for f in func_filter:
                    if equal_function(func, f) and \
                            df.cols.dtypes(col_name)[col_name] == data_type:
                        return True
            return False

        columns = parse_columns(df, columns)
        funcs = val_to_list(funcs)
        exprs = {}

        multi = [df.functions.min, df.functions.max, df.functions.stddev,
                 df.functions.mean, df.functions.variance, df.functions.percentile_agg]

        for func in funcs:
            # Create expression for functions that accepts multiple columns
            if equal_function(func, multi):
                exprs.update(func(columns, args)(df))
            # If not process by column
            else:
                for col_name in columns:
                    # If the key exist update it
                    if not _filter(col_name, func):
                        if col_name in exprs:
                            exprs[col_name].update(func(col_name, args)(df))
                        else:
                            exprs[col_name] = func(col_name, args)(df)

        result = {}

        for k, v in exprs.items():
            if k in result:
                result[k].update(v)
            else:
                result[k] = {}
                result[k] = v

        # Convert to list
        result = [r for r in result.items()]

        return result

    # TODO: Check if we must use * to select all the columns
    @dispatch(object, object)
    def rename(self, columns_old_new=None, func=None):
        """"
        Changes the name of a column(s) dataFrame.
        :param columns_old_new: List of tuples. Each tuple has de following form: (oldColumnName, newColumnName).
        :param func: can be lower, upper or any string transformation function
        """

        df = self.df

        # Apply a transformation function
        if is_list_of_tuples(columns_old_new):
            validate_columns_names(self, columns_old_new)
            for col_name in columns_old_new:

                old_col_name = col_name[0]
                if is_int(old_col_name):
                    old_col_name = self.df.schema.names[old_col_name]
                if func:
                    old_col_name = func(old_col_name)

                current_meta = self.df.meta.get()
                # DaskColumns.set_meta(col_name, "optimus.transformations", "rename", append=True)
                # TODO: this seems to the only change in this function compare to pandas. Maybe this can be moved to a base class

                new_column = col_name[1]
                if old_col_name != col_name:
                    df = df.rename({old_col_name: new_column})

                df = df.meta.preserve(self.df, value=current_meta)

                df = df.meta.rename((old_col_name, new_column))

        return df

    @dispatch(list)
    def rename(self, columns_old_new=None):
        return self.rename(columns_old_new, None)

    @dispatch(object)
    def rename(self, func=None):
        return self.rename(None, func)

    @dispatch(str, str, object)
    def rename(self, old_column, new_column, func=None):
        return self.rename([(old_column, new_column)], func)

    @dispatch(str, str)
    def rename(self, old_column, new_column):
        return self.rename([(old_column, new_column)], None)

    @staticmethod
    def date_transform(input_cols, current_format=None, output_format=None, output_cols=None):
        raise NotImplementedError('Look at me I am dask now')

    def fill_na(self, input_cols, value=None, output_cols=None):
        """
        Replace null data with a specified value
        :param input_cols: '*', list of columns names or a single column name.
        :param output_cols:
        :param value: value to replace the nan/None values
        :return:
        """

        # def fill_none_numeric(_value):
        #     if pd.isnan(_value):
        #         return value
        #     return _value

        df = self.df

        input_cols = parse_columns(df, input_cols)
        check_column_numbers(input_cols, "*")
        output_cols = get_output_cols(input_cols, output_cols)

        for output_col in output_cols:
            df[output_col].fillna(value=value, axis=1)
            # df[output_col] = df[output_col].apply(fill_none_numeric, meta=(output_col, "object") )
            # df[output_col] = df[output_col].mask( df[output_col].isin([0,False,None,[],{}]) , value ) 

        return df

    def count_by_dtypes(self, columns, infer=False, str_funcs=None, int_funcs=None, mismatch=None):
        df = self.df
        columns = parse_columns(df, columns)
        dtypes = df.cols.dtypes()

        result = {}
        for col_name in columns:
            df_result = df[col_name].apply(Infer.parse_dask, args=(col_name, infer, dtypes, str_funcs, int_funcs),
                                           meta=str).compute()

            result[col_name] = dict(df_result.value_counts())

        if infer is True:
            for k in result.keys():
                result[k] = fill_missing_var_types(result[k])
        else:
            result = self.parse_profiler_dtypes(result)

        return result

    @staticmethod
    def lower(input_cols, output_cols=None):

        def _lower(col_name, args):
            return col_name[args].str.lower()

        return DaskBaseColumns.apply(input_cols, _lower, func_return_type=str,
                                     filter_col_by_dtypes=["string", "object"],
                                     output_cols=output_cols)

    @staticmethod
    def upper(input_cols, output_cols=None):

        def _upper(col_name, args):
            return col_name[args].str.upper()

        return DaskBaseColumns.apply(input_cols, _upper, func_return_type=str,
                                     filter_col_by_dtypes=["string", "object"],
                                     output_cols=output_cols)

    @staticmethod
    def trim(input_cols, output_cols=None):

        def _trim(_df, args):
            return _df[args].str.strip()

        return DaskBaseColumns.apply(input_cols, _trim, func_return_type=str, filter_col_by_dtypes=["string", "object"],
                                     output_cols=output_cols)

    def apply(self, input_cols, func=None, func_return_type=None, args=None, func_type=None, when=None,
              filter_col_by_dtypes=None, output_cols=None, skip_output_cols_processing=False, meta="apply"):

        df = self.df

        input_cols = parse_columns(df, input_cols, filter_by_column_dtypes=filter_col_by_dtypes,
                                   accepts_missing_cols=True)
        check_column_numbers(input_cols, "*")

        if skip_output_cols_processing:
            output_cols = val_to_list(output_cols)
        else:
            output_cols = get_output_cols(input_cols, output_cols)

        if output_cols is None:
            output_cols = input_cols

        args = val_to_list(args)

        for input_col, output_col in zip(input_cols, output_cols):
            print("func_return_type", func_return_type)
            if func_return_type is None:
                _meta = df[input_col]
            else:
                if "int" in func_return_type:
                    return_type = int
                elif "float" in func_return_type:
                    return_type = float
                elif "bool" in func_return_type:
                    return_type = bool
                else:
                    return_type = object
                _meta = df[input_col].astype(return_type)

            df[output_col] = df[input_col].apply(func, meta=_meta, args=args)

        return df

    # TODO: Maybe should be possible to cast and array of integer for example to array of double
    def cast(self, input_cols=None, dtype=None, output_cols=None, columns=None):
        """
        Cast a column or a list of columns to a specific data type
        :param input_cols: Columns names to be casted
        :param output_cols:
        :param dtype: final data type
        :param columns: List of tuples of column names and types to be casted. This variable should have the
                following structure:
                colsAndTypes = [('columnName1', 'integer'), ('columnName2', 'float'), ('columnName3', 'string')]
                The first parameter in each tuple is the column name, the second is the final datatype of column after
                the transformation is made.
        :return: Dask DataFrame
        """

        df = self.df
        _dtypes = []

        def _cast_int(value):
            try:
                return int(value)
            except ValueError:
                return None

        def _cast_float(value):
            try:
                return float(value)
            except ValueError:
                return None

        def _cast_bool(value):
            if value is None:
                return None
            else:
                return bool(value)

        def _cast_str(value):
            try:
                return value.astype(str)
            except:
                return str(value)

        # Parse params
        if columns is None:
            input_cols = parse_columns(df, input_cols)
            if is_list(input_cols) or is_one_element(input_cols):
                output_cols = get_output_cols(input_cols, output_cols)
                for _ in builtins.range(0, len(input_cols)):
                    _dtypes.append(dtype)
        else:
            input_cols = list([c[0] for c in columns])
            if len(columns[0]) == 2:
                output_cols = get_output_cols(input_cols, output_cols)
                _dtypes = list([c[1] for c in columns])
            elif len(columns[0]) == 3:
                output_cols = list([c[1] for c in columns])
                _dtypes = list([c[2] for c in columns])

            output_cols = get_output_cols(input_cols, output_cols)

        for input_col, output_col, dtype in zip(input_cols, output_cols, _dtypes):
            if dtype == 'int':
                df.cols.apply(input_col, func=_cast_int, func_return_type="int", output_cols=output_col)
                # df[output_col] = df[input_col].apply(func=_cast_int, meta=df[input_col])
            elif dtype == 'float':
                df.cols.apply(input_col, func=_cast_float, func_return_type="float", output_cols=output_col)
                # df[output_col] = df[input_col].apply(func=, meta=df[input_col])
            elif dtype == 'bool':
                df.cols.apply(input_col, func=_cast_bool, output_cols=output_col)
                # df[output_col] = df[input_col].apply(func=, meta=df[input_col])
            else:
                df.cols.apply(input_col, func=_cast_str, func_return_type="object", output_cols=output_col)
                # df[output_col] = df[input_col].apply(func=_cast_str, meta=df[input_col])
            df[output_col].odtype = dtype

        return df

    def cast_type(self, input_cols=None, dtype=None, output_cols=None, columns=None):
        """
        Cast a column or a list of columns to a specific data type
        :param input_cols: Columns names to be casted
        :param output_cols:
        :param dtype: final data type
        :param columns: List of tuples of column names and types to be casted. This variable should have the
                following structure:
                colsAndTypes = [('columnName1', 'int64'), ('columnName2', 'float'), ('columnName3', 'int32')]
                The first parameter in each tuple is the column name, the second is the final datatype of column after
                the transformation is made.
        :return: Dask DataFrame
        """

        df = self.df
        _dtypes = []

        # Parse params
        if columns is None:
            input_cols = parse_columns(df, input_cols)
            if is_list(input_cols) or is_one_element(input_cols):
                output_cols = get_output_cols(input_cols, output_cols)
                for _ in builtins.range(0, len(input_cols)):
                    _dtypes.append(dtype)
        else:
            input_cols = list([c[0] for c in columns])
            if len(columns[0]) == 2:
                output_cols = get_output_cols(input_cols, output_cols)
                _dtypes = list([c[1] for c in columns])
            elif len(columns[0]) == 3:
                output_cols = list([c[1] for c in columns])
                _dtypes = list([c[2] for c in columns])

            output_cols = get_output_cols(input_cols, output_cols)

        for input_col, output_col, dtype in zip(input_cols, output_cols, _dtypes):
            df[output_col] = df[input_col].astype(dtype=dtype)

        return df

    def nest(self, input_cols, shape="string", separator="", output_col=None):
        """
        Concat multiple columns to one with the format specified
        :param input_cols: columns to be nested
        :param separator: char to be used as separator at the concat time
        :param shape: final data type, 'array', 'string' or 'vector'
        :param output_col:
        :return: Dask DataFrame
        """

        df = self.df
        input_cols = parse_columns(df, input_cols)
        output_col = parse_columns(df, output_col, accepts_missing_cols=True)
        check_column_numbers(output_col, 1)

        def _nest_string(value):
            v = value[input_cols[0]].astype(str)
            for i in builtins.range(1, len(input_cols)):
                v = v + separator + value[input_cols[i]].astype(str)
            return v

        def _nest_array(value):
            v = value[input_cols[0]].astype(str)
            for i in builtins.range(1, len(input_cols)):
                v += ", " + value[input_cols[i]].astype(str)
            return "[" + v + "]"

        if shape == "string":
            df = df.assign(**{output_col[0]: _nest_string})
        else:
            df = df.assign(**{output_col[0]: _nest_array})

        return df

    def unnest(self, input_cols, separator=None, splits=0, index=None, output_cols=None):
        """
        Split an array or string in different columns
        :param input_cols: Columns to be un-nested
        :param output_cols: Resulted on or multiple columns  after the unnest operation [(output_col_1_1,output_col_1_2), (output_col_2_1, output_col_2]
        :param separator: char or regex
        :param splits: Number of rows to un-nested. Because we can not know beforehand the number of splits
        :param index: Return a specific index per columns. [{1,2},()]
        """

        # Special case. A dot must be escaped
        if separator == ".":
            separator = "\\."

        df = self.df

        input_cols = parse_columns(df, input_cols)
        output_cols = get_output_cols(input_cols, output_cols)

        def spread_split(_row, _output_col, _splits):

            for i in range(_splits):
                try:
                    value = _row[_output_col + "_" + str(_splits - 1)][i]
                except IndexError:
                    value = None
                except TypeError:
                    value = None
                _row[_output_col + "_" + str(i)] = value
            return _row

        for idx, (input_col, output_col) in enumerate(zip(input_cols, output_cols)):

            if separator is None:
                RaiseIt.value_error(separator, "regular expression")

            df = df.assign(**{output_col + "_" + str(i): "" for i in range(splits - 1)})
            df[output_col + '_' + str(splits - 1)] = df[input_col].astype(str).str.split(separator, splits - 1)
            df = df.apply(spread_split, axis=1, output_col=output_col, splits=splits, meta=df)

        return df

    def replace(self, input_cols, search=None, replace_by=None, search_by="chars", output_cols=None):
        """
        Replace a value, list of values by a specified string
        :param input_cols: '*', list of columns names or a single column name.
        :param output_cols:
        :param search: Values to look at to be replaced
        :param replace_by: New value to replace the old one
        :param search_by: Can be "full","words","chars" or "numeric".
        :return: Dask DataFrame
        """
        df = self.df

        # TODO check if .contains can be used instead of regexp
        def func_chars_words(_df, _input_col, _output_col, _search, _replace_by):
            # Reference https://www.oreilly.com/library/view/python-cookbook/0596001673/ch03s15.html

            # Create as dict
            search_and_replace_by = None
            if is_list(_search):
                search_and_replace_by = {s: _replace_by for s in _search}
            elif is_one_element(_search):
                search_and_replace_by = {_search: _replace_by}

            search_and_replace_by = {str(k): str(v) for k, v in search_and_replace_by.items()}

            # Create a regular expression from all of the dictionary keys
            regex = None
            if search_by == "chars":
                regex = re.compile("|".join(map(re.escape, search_and_replace_by.keys())))
            elif search_by == "words":
                regex = re.compile(r'\b%s\b' % r'\b|\b'.join(map(re.escape, search_and_replace_by.keys())))

            def multiple_replace(value, _search_and_replace_by):
                if value is not None:
                    return regex.sub(lambda match: _search_and_replace_by[match.group(0)], str(value))
                else:
                    return None

            return _df.cols.apply(_input_col, multiple_replace, "str", search_and_replace_by,
                                  output_cols=_output_col)

        def func_full(_df, _input_col, _output_col, _search, _replace_by):
            _search = val_to_list(_search)

            if _input_col != _output_col:
                _df[_output_col] = _df[_input_col]

            _df[_output_col] = _df[_output_col].mask(_df[_output_col].isin(_search), _replace_by)
            return _df

        func = None
        if search_by == "full" or search_by == "numeric":
            func = func_full
        elif search_by == "chars" or search_by == "words":
            func = func_chars_words
        else:
            RaiseIt.value_error(search_by, ["chars", "words", "full", "numeric"])

        filter_dtype = None
        if search_by in ["chars", "words", "full"]:
            filter_dtype = df.constants.STRING_TYPES
        elif search_by == "numeric":
            filter_dtype = df.constants.NUMERIC_TYPES

        input_cols = parse_columns(self, input_cols, filter_by_column_dtypes=filter_dtype)

        check_column_numbers(input_cols, "*")
        output_cols = get_output_cols(input_cols, output_cols)

        df = self
        for input_col, output_col in zip(input_cols, output_cols):
            df = func(df, input_col, output_col, search, replace_by)

        return df

    def is_numeric(self, col_name):
        """
        Check if a column is numeric
        :param col_name:
        :return:
        """
        df = self.df
        # TODO: Check if this is the best way to check the data type
        if np.dtype(df[col_name]).type in [np.int64, np.int32, np.float64]:
            result = True
        else:
            result = False
        return result

    # @staticmethod
    # def hist(columns, buckets=20):
    #     result = DaskColumns.agg_exprs(columns, self.functions.hist_agg, self, buckets, None)
    #     return result

    def frequency(self, columns, n=10, percentage=False, total_rows=None):
        df = self.df
        columns = parse_columns(df, columns)
        q = []
        for col_name in columns:
            q.append({col_name: [{"value": k, "count": v} for k, v in
                                 df[col_name].value_counts().nlargest(n).iteritems()]})

        result = dd.compute(*q)
        # From list of tuples to dict
        final_result = {}
        for i in result:
            for x, y in i.items():
                final_result[x] = y

        print(result)
        if percentage is True:
            if total_rows is None:
                total_rows = df.rows.count()
                for c in final_result:
                    c["percentage"] = round((c["count"] * 100 / total_rows), 2)

        return result

    def schema_dtype(self, columns="*"):
        """
        Return the column(s) data type as Type
        :param columns: Columns to be processed
        :return:
        """
        df = self.df
        # if np.dtype(self[col_name]).type in [np.int64, np.int32, np.float64]:
        #     result = True
        #
        columns = parse_columns(self, columns)
        return format_dict([np.dtype(df[col_name]).type for col_name in columns])

    def select(self, columns="*", regex=None, data_type=None, invert=False):
        """
        Select columns using index, column name, regex to data type
        :param columns:
        :param regex: Regular expression to filter the columns
        :param data_type: Data type to be filtered for
        :param invert: Invert the selection
        :return:
        """
        df = self.df
        columns = parse_columns(df, columns, is_regex=regex, filter_by_column_dtypes=data_type, invert=invert)
        if columns is not None:
            df = df[columns]
            # Metadata get lost when using select(). So we copy here again.
            # df.ext.meta = self.ext.meta
            result = df
        else:
            result = None

        return result

