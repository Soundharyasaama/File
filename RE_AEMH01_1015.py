import pandas as pd
import sys # Commuicate with interpreter
import re
import pdb  # 
import utilsk as utils
import utils_C4591015 as studyutils
import warnings
warnings.filterwarnings('ignore')
from base import BaseSDQApi
import traceback
import tqdm
import logging

class RE_AEMH01_1015(BaseSDQApi):
    domain_list = ['AE', 'MH']  

    def execute(self):
        study = self.study_id
        
        total_count = 0
        domain_list = ['AE', 'MH']
        subjects = self.get_subjects(study, domain_list = domain_list, per_page = 10000)
        
        for subject in subjects:
            try:
                flatten_data = self.get_flatten_data(study, subject, per_page=10000, domain_list = domain_list)
                ae_df = pd.DataFrame(flatten_data['AE'])
                ae_df.columns = map(str.lower, ae_df.columns)            
                mh_df = pd.DataFrame(flatten_data['MH'])
                mh_df.columns = map(str.lower, mh_df.columns)
#                 if 'DS' in flatten_data:                    
#                     ds_df = pd.DataFrame(flatten_data['DS'])
#                     ds_df.columns = map(str.lower, ds_df.columns)
#                     ds_flag = True
#                 else:
#                     ds_flag = False
                
                ae_df['modif_dts'] = pd.to_datetime(ae_df['modif_dts'])

                # Filters FORMREFNAME
                mh_df = mh_df[mh_df['formrefname'] == 'MH001']
                new_ae_df = ae_df[ae_df['formrefname'] == 'AE001']
                   
                # Check if MHDECOD is present
                mhdecod_uniques = mh_df['mhllt_001'].unique().tolist()
                mhdecod_uniques = [i for i in mhdecod_uniques if i != '' and i != " " and i != 'null']
                aedecod_uniques = ae_df['aellt_001'].unique().tolist()
                aedecod_uniques = [i for i in aedecod_uniques if i != '' and i != " " and i != 'null']
                if len(mhdecod_uniques) == 0 or len(aedecod_uniques) == 0:
                    continue
                new_ae_df = new_ae_df[new_ae_df['aellt_001'].isin(mhdecod_uniques)]
                
                ae_list = ['WORSENING', 'EXACERBATION']  

                result_rows = []
                for ind, row in new_ae_df.iterrows():
                    aeterm = row['aeterm_001']
                    count = 0
                    for piv_ae_term in ae_list:
                        if type(aeterm) == str:
                            # RegEx to remove special characters
                            if utils.check_similar_term(piv_ae_term, aeterm) == False: #
                                count += 1

                    if count == 2:
                        result_rows.append(row) 

                result_df = pd.DataFrame(result_rows)
                sub_cat = 'RE_AEMH01'
                sub_cat_nm_report = 'RE_AEMH01_1015'
                if result_df.shape[0] > 0:

                    for i, (_, row) in enumerate(result_df.iterrows()): #
                        aedecod = row['aellt_001']
                        new_mh_df = mh_df[mh_df['mhllt_001'] == aedecod].iloc[[0]] 
                        subcate_report_dict = {}
                        report_dict = {}
                        
#                         if ds_flag == False:
#                             d = {'formrefname' : 'week1'}
#                             ds_df = pd.DataFrame([d])
                            
                        piv_rec = {'AE' : result_df.iloc[[i]], 'MH' : new_mh_df}#, 'DS' : ds_df.iloc[[0]]}
                        
                        for dom, cols in studyutils.subcat_cols[sub_cat_nm_report].items():
                            piv_df = piv_rec[dom]
                            present_col = [col for col in cols if col in piv_df.columns.tolist()]
                            rep_df = piv_df[present_col]
                            if dom != 'DS':
                                rep_df['deeplink'] = utils.get_deeplink(study, piv_df)
                            rep_df = rep_df.rename(columns= studyutils.subcat_rename_cols[sub_cat_nm_report][dom])
                            report_dict[dom]= rep_df.to_json(orient= 'records')  #
                            
                        subcate_report_dict[sub_cat] =  report_dict

                        aeterm = row['aeterm_001']
                        
                        total_count += 1
                        payload = {
                            "subcategory": sub_cat,
                            "query_text": self.get_query_text_json(study, sub_cat, params = [aeterm]),
                            "form_index": row['form_index'],
                            "question_present": self.get_subcategory_json(study, sub_cat),
                            "modif_dts": str(row['modif_dts']),  
                            "stg_ck_event_id": row['ck_event_id'],
                            "report" : subcate_report_dict
                        }
#                         print(subject, payload)
                        self.insert_query(study, subject, payload)
                        

            except Exception as e:
                logging.exception(e)
                                
if __name__ == '__main__':
    study_id = sys.argv[1]
    rule_id = sys.argv[2]
    version = sys.argv[3]
    rule = RE_AEMH01_1015(study_id, rule_id, version)
    rule.run()
