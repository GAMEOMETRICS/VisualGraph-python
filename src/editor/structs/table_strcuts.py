#coding:utf-8
import sys

sys.path.append('..')

from vg_env import register_struct,TableStruct

# 一个example

@register_struct
class table_eigen(TableStruct):
    columns = 'Journal ID,Pnum In Pre2Year,Indegree,Weighted InDegree,Outdegree,Weighted OutDegree,Closeness,Out Closeness,Betweenness,Out Betweenness,Eigenvector,Out Eigenvector,pnum,cit,cit2,cit5,IFI'.split(',')

@register_struct
class table_ABS(TableStruct):
    columns: list = 'paper_id,year,journal_id,teamsize,age_mean,age_std,pnum_mean,pnum_std,cn_mean,cn_std,rank_mean,rank_std,freshness_DIV,c2_DIV,c5_DIV,c10_DIV,d2_DIV,d5_DIV,d10_DIV,subject_DIV,variety,balance,disparsity,impact_diversity,num_of_refs,d2,d5,d10,c2,c5,c10'.split(',')
