import zipfile
import xml.etree.ElementTree
from pypdf import PdfReader
from html.parser import HTMLParser
import os
import json
import math
import subprocess

class MyHTMLParser(HTMLParser):
    def __init__(self, *, convert_charrefs: bool = True) -> None:
        super().__init__(convert_charrefs=convert_charrefs)
        self.ret=''

    def handle_data(self, data: str) -> None:
        self.ret+=data

def get_text_docx(file_path):
    WORD_NAMESPACE = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    PARA = WORD_NAMESPACE + 'p'
    TEXT = WORD_NAMESPACE + 't'
    TABLE = WORD_NAMESPACE + 'tbl'
    ROW = WORD_NAMESPACE + 'tr'
    CELL = WORD_NAMESPACE + 'tc'

    res=''
    with zipfile.ZipFile(file_path) as docx:
        tree = xml.etree.ElementTree.XML(docx.read('word/document.xml'))
        # u word/media imas slike ako ikad zatreba
    
    for node in tree.iter(TEXT):
        res+=node.text+' '
   
    return res

def get_text_txt(file_path):
    res=''
    file=open(file_path,"r",encoding='utf-8')
    res=file.read()
    file.close()
    return res

def get_text_pdf(file_path):
    res=''
    reader = PdfReader(file_path)
    for page in reader.pages:
        res+=page.extract_text()+' '
    return res

def get_text_xml(file_path):
    file=open(file_path,"r",encoding="utf-8")
    xml_text=file.read()
    file.close()
    parser=MyHTMLParser()
    parser.feed(xml_text)
    return parser.ret

def calc_tf(text:str):
    all_terms=text.split()
    unique_terms=set(all_terms)
    term_dict={}
    for term in unique_terms:
        term_dict[term]=all_terms.count(term)/len(all_terms)
    return term_dict,unique_terms

def index_dir(dir_path):
    idf_info={}
    file_cnt=0
    fucked_files=[]
    my_dir=os.path.join(dir_path,".indexing")
    if ~(os.path.isdir(my_dir)):
        try:
            os.mkdir(my_dir)
        except:
            pass
    all_files=os.listdir(dir_path)
    for f in all_files:
        file=os.path.join(dir_path,f)
        if file==my_dir:
            continue
        if os.path.isdir(file):
            new_files=os.listdir(file)
            fixed_new_files=[]
            for new_file in new_files:
                fixed_new_files.append(os.path.join(dir_path,file,new_file))
            all_files.extend(fixed_new_files)
        else:
            text=""
            file_type=file[file.rfind(".")+1:len(file)]
            try:
                if file_type=="html" or file_type=="xhtml" or file_type=='xml': text=get_text_xml(file)
                elif file_type=="doc" or file_type=="docx" : text=get_text_docx(file)
                elif file_type=="pdf": text=get_text_pdf(file)
                else : text=get_text_txt(file)
            except:
                fucked_files.append(file)
                continue

            file_dict,new_terms=calc_tf(text)
            new_file=open(os.path.join(my_dir,file.replace('\\','_')),"w",encoding='utf-8')
            new_file.write(json.dumps(file_dict))
            print("Wrote new file")
            new_file.close()
            file_cnt+=1

            for term in new_terms:
                    if term in idf_info:
                        idf_info[term]=idf_info.get(term)+1
                    else: idf_info[term]=1

    for term in idf_info:
        idf_info[term]=math.log10(file_cnt/idf_info.get(term))
    idf_file=open(my_dir+"/idf","w")
    idf_file.write(json.dumps(idf_info))
    idf_file.close()
    print(len(fucked_files))

def search(query,dir_path):
    idf_file=open(os.path.join(dir_path,".indexing/idf"),encoding='utf-8')
    idf_dict=json.loads(idf_file.read())
    search_terms=query.split(" ")
    results=[]
    files=os.listdir(os.path.join(dir_path,".indexing"))
    for file in files:
        if file=='idf': continue
        abs_path=os.path.join(dir_path,".indexing",file)
        f=open(abs_path,"r",encoding='utf-8')
        cur_dict=json.loads(f.read())
        cur_tf_idf=0
        for term in search_terms:
            if(term in cur_dict):
                cur_tf_idf+=cur_dict[term]*idf_dict[term]
        results.append((abs_path,cur_tf_idf))
    results.sort(key=lambda x:x[1],reverse=True)
    return results

def get_full_path(text):
    called_for=(text.split(".indexing"))[0]
    split=called_for.split('\\')
    last_in_called=split[len(split)-2]
    to_add=text.split('_'+last_in_called+"_")[1]
    return os.path.join(called_for,to_add.replace('_','\\'))
    
"""
if __name__=='__main__':
    #index_dir("C:\\Users\\ps200536d\\Desktop\\test")
    res=search("linear interpolation","C:\\Users\\ps200536d\\Desktop\\browser\\folder_browser\\test")
    os.startfile(get_full_path(res[0][0]))
"""