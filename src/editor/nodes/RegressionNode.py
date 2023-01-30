#coding:utf-8
'''
尽量包含所有常用的回归模型，并给出什么情况下适用，什么情况下不适用。

1. 线性回归
2. 逻辑斯蒂回归
3. 多项式回归
4. 逐步回归
5. 岭回归
6. lasso回归
7. elasticnet回归

'''
import sys

sys.path.append('..')
from vg_dtypes import VGDtypes
from vg_env import register_node
from vg_config import NodeConfig
from statsmodels.stats.outliers_influence import variance_inflation_factor

import pandas as pd
from statsmodels.discrete.discrete_model import NegativeBinomial, Poisson
from statsmodels.discrete.count_model import ZeroInflatedPoisson, ZeroInflatedNegativeBinomialP, ZeroInflatedGeneralizedPoisson
from statsmodels.regression.linear_model import OLS
import statsmodels.api as sm
import numpy as np
import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)

NodeConfig.node_title_back_color['Regression Analysis'] = '#ff843f'


class RegressionResultTableWrapper:
    '''对statsmodels的结果进行封装'''
    def __init__(self, result, labels=None):

        self.result = result
        self.labels = labels

    def summary(self):
        return self.result.summary()

    def table(self):
        dic = {}
        dic['AIC'] = self.result.aic
        dic['BIC'] = self.result.bic
        # dic['F_pvalue'] = self.result.f_pvalue
        # dic['params'] = type(self.result.params)
        params = self.result.params
        pvalues = self.result.pvalues
        assert (len(params) == len(pvalues))

        for label in self.labels:

            param = params.loc[label]
            pvalue = pvalues.loc[label]
            dic[label] = '{:.4f}\n({:})'.format(param,
                                                self.pvalue_star(pvalue))

        return pd.DataFrame({'Attribute': dic.keys(), 'Values': dic.values()})

    def pvalue_star(self, pvalue):
        if pvalue >= 0.05:
            return '{:.2f}'.format(pvalue)
        elif pvalue < 0.001:
            return '***'
        elif pvalue < 0.01:
            return '**'
        elif pvalue < 0.05:
            return '*'


@register_node(name='Table VIF',
               package='Regression Analysis',
               output={'VIFs': VGDtypes.Table})
def VIF_of_Table(data: VGDtypes.Table):
    '''
    参考 https://github.com/statsmodels/statsmodels/issues/2376 以及 https://stackoverflow.com/questions/42658379/variance-inflation-factor-in-python
    在使用statsmodel的VIF计算时，需要在数据上添加constant。

    VIF结果，一般情况下小于5（特殊情况下可以认为小于10）可以认为自变量不存在多重共线性。
    '''

    new_data = data.assign(const=1)
    columns = new_data.columns
    VIFs = []
    for i in range(0, len(columns) - 1):
        VIF = variance_inflation_factor(new_data.values, i)
        VIFs.append(VIF)

    return pd.DataFrame({'Variable': columns[:-1], 'VIF': VIFs})


@register_node(name='Table Column VIF',
               package='Regression Analysis',
               output={'VIFs': VGDtypes.Table})
def variance_infloation_factor(data: VGDtypes.Table, cols: VGDtypes.Array):
    '''
    参考 https://github.com/statsmodels/statsmodels/issues/2376 以及 https://stackoverflow.com/questions/42658379/variance-inflation-factor-in-python
    在使用statsmodel的VIF计算时，需要在数据上添加constant。

    VIF结果，一般情况下小于5（特殊情况下可以认为小于10）可以认为自变量不存在多重共线性。
    '''

    new_data = data[cols]
    new_data = new_data.assign(const=1)
    columns = new_data.columns
    VIFs = []
    for i in range(len(columns) - 1):
        VIF = variance_inflation_factor(new_data.values, i)
        VIFs.append(VIF)
    return pd.DataFrame({'Variable': columns[:-1], 'VIF': VIFs})


@register_node(name='Negative Binomial Regression',
               package='Regression Analysis',
               output={'Result': VGDtypes.Table})
def NegativeBinomialRegression(data: VGDtypes.Table,
                               independent_variables: VGDtypes.Array,
                               dependent_variable: VGDtypes.String,
                               not_normalized: VGDtypes.Bool):
    new_data = pd.DataFrame()
    if not not_normalized:
        for iv in independent_variables:
            new_data[iv] = (data[iv] - data[iv].min()) / (data[iv].max() -
                                                          data[iv].min())
    # formula = f'{dependent_variable} ~ {" + ".join(independent_variables)}'
    # print(formula)
    # nb_model = NegativeBinomial.from_formula(formula=formula, data=data)
    # res = nb_model.fit_regularized()
    # print(res.summary2())

    exog = sm.add_constant(new_data[independent_variables])
    endog = data[dependent_variable]
    glm_nb_model = sm.GLM(endog, exog, family=sm.families.NegativeBinomial())
    res = glm_nb_model.fit()

    rrw = RegressionResultTableWrapper(res, labels=independent_variables)

    return rrw.table()


@register_node(name='Zero Inflated Negative Binomial Regression',
               package='Regression Analysis',
               output={'Result': VGDtypes.Table})
def ZeroInflatedNegativeBinomialRegression(
        data: VGDtypes.Table, independent_variables: VGDtypes.Array,
        dependent_variable: VGDtypes.String, not_normalized: VGDtypes.Bool):
    new_data = pd.DataFrame()
    if not not_normalized:
        for iv in independent_variables:
            new_data[iv] = (data[iv] - data[iv].min()) / (data[iv].max() -
                                                          data[iv].min())
    # formula = f'{dependent_variable} ~ {" + ".join(independent_variables)}'
    # print(formula)
    # nb_model = NegativeBinomial.from_formula(formula=formula, data=data)
    # res = nb_model.fit_regularized()
    # print(res.summary2())

    exog = sm.add_constant(new_data[independent_variables])
    endog = data[dependent_variable]
    glm_nb_model = ZeroInflatedNegativeBinomialP(
        endog, exog, family=sm.families.NegativeBinomial())
    res = glm_nb_model.fit_regularized()

    rrw = RegressionResultTableWrapper(res, labels=independent_variables)

    return rrw.table()


@register_node(name='Poission Regression',
               package='Regression Analysis',
               output={'Result': VGDtypes.Table})
def PoissonRegression(data: VGDtypes.Table,
                      independent_variables: VGDtypes.Array,
                      dependent_variable: VGDtypes.String,
                      not_normalized: VGDtypes.Bool):

    # TODO 添加一个O检验，判断是使用泊松还是使用负二项回归
    # formula = f'{dependent_variable} ~ {" + ".join(independent_variables)}'
    # pn_model = Poisson.from_formula(formula=formula, data=data)
    # res = pn_model.fit_regularized()
    new_data = pd.DataFrame()
    if not not_normalized:
        for iv in independent_variables:
            new_data[iv] = (data[iv] - data[iv].min()) / (data[iv].max() -
                                                          data[iv].min())

    exog = sm.add_constant(new_data[independent_variables])
    endog = data[dependent_variable]
    glm_nb_model = sm.GLM(endog, exog, family=sm.families.Poisson())
    res = glm_nb_model.fit()

    rrw = RegressionResultTableWrapper(res, labels=independent_variables)

    return rrw.table()


@register_node(name='Zero Inflated Poission Regression',
               package='Regression Analysis',
               output={'Result': VGDtypes.Table})
def ZIPRegression(data: VGDtypes.Table, independent_variables: VGDtypes.Array,
                  dependent_variable: VGDtypes.String,
                  not_normalized: VGDtypes.Bool):

    # TODO 添加一个O检验，判断是使用泊松还是使用负二项回归
    # formula = f'{dependent_variable} ~ {" + ".join(independent_variables)}'
    # pn_model = Poisson.from_formula(formula=formula, data=data)
    # res = pn_model.fit_regularized()
    new_data = pd.DataFrame()
    if not not_normalized:
        for iv in independent_variables:
            new_data[iv] = (data[iv] - data[iv].min()) / (data[iv].max() -
                                                          data[iv].min())

    exog = sm.add_constant(new_data[independent_variables])
    endog = data[dependent_variable]
    glm_nb_model = ZeroInflatedPoisson(endog,
                                       exog,
                                       family=sm.families.Poisson())
    res = glm_nb_model.fit_regularized()

    rrw = RegressionResultTableWrapper(res, labels=independent_variables)

    return rrw.table()


@register_node(name='OLS Regression',
               package='Regression Analysis',
               output={'Result': VGDtypes.Table})
def OLSRegression(data: VGDtypes.Table, independent_variables: VGDtypes.Array,
                  dependent_variable: VGDtypes.String):
    formula = f'{dependent_variable} ~ {" + ".join(independent_variables)}'
    rm_ols = OLS.from_formula(formula=formula, data=data).fit()

    rrw = RegressionResultTableWrapper(rm_ols, labels=independent_variables)

    return rrw.table()
