import ssl
import socket
import re
import json
import os
import math

def get_html(host,page):
    port=443

    context=ssl.create_default_context()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    s = context.wrap_socket(s, server_side=False,server_hostname=host)

    request="GET " + page + " HTTP/1.1\r\nHost: " + host + "\r\nConnection: close\r\n\r\n"

    s.sendall(bytes(request,encoding="utf-8"))

    response=b""
    while True:
        chunk=s.recv(1024)
        if len(chunk)==0:
            s.close()
            break
        response=response+chunk
   
    return str(response,encoding="utf-8")


def read_https_header(html):
    out=''
    for char in html:
        if(char=='<') :return out,html.replace(out,'')
        out=out+char

def parse_html(html) :  
    output=''
    tags_with_break={'h ','p','li','h1','h2','h3','h4','h5','h6','title','div'}
    tags_without_close={'br','meta',"link","img","hr"}
    buffer=''
    opened=False
    opened_tags=[]
    links=[]
    script=''
    i=0
    while(i<len(html)):
        if(html[i]=='<'):
            opened=True
            i+=1
            while(html[i] != ' ' and html[i]!='>'):
                buffer=buffer+html[i]
                i=i+1

            if(len(buffer)>1):
                if(buffer[0:1]=='!-'):
                    i=parse_comment(html,i,buffer)

            if(buffer=='a'):
                href_buff=''
                while(html[i]!='>'): 
                    href_buff+=html[i]
                    i+=1
                links+=get_links(href_buff)
            
            if(html[i]=='>') :
                opened=False
                i+=1

            if(buffer[0]=='/') :
                if(buffer[1:len(buffer)] in tags_with_break):
                    output+='\n'
                opened_tags.pop(len(opened_tags)-1)
                buffer=''
            elif(buffer[0]!='!'):
                if(buffer in tags_without_close):
                    if(buffer=='br'): output+='\n'
                else:
                    opened_tags.append(buffer)
                buffer=''
            elif(buffer[0]=='!'): buffer=''
        elif(~opened) :
            if(len(opened_tags)>0):
                if(opened_tags[len(opened_tags)-1]=='script'):
                    i+=1
                    script+=html[i]
                    continue
            if(html[i]!='\n' and html[i]!='\t'):
                output+=html[i]
            i+=1
        if(opened):
            while(html[i]!='>'): 
                i+=1
                if(i>len(html)-1) :return output
            i+=1
            opened=False
        
        
    return output,script,links
        
def parse_comment(html,i,buffer):
    new_buff=buffer
    regex=".*-->$"
    while(re.search(regex,new_buff)==None):
        new_buff+=html[i]
        i+=1
    return i-1

def get_links(html):
    urls = re.findall(r'href=[\'"]?([^\'"# >]+)', html)
    return urls

def calc_tf(text):
    
    all_terms=re.split(r" |\n|\r",text)
    unique_terms=set(all_terms)
    term_dict={}
    for term in unique_terms:
        term_dict[term]=all_terms.count(term)/len(all_terms)
    return term_dict,unique_terms
        
def search(query):
    f=open("idf")
    idf=json.loads(f.read())
    search_terms=query.split(" ")
    order=[]
    for filename in os.listdir("sites"):
        file=open(os.path.join("sites",filename))
        try:
            cur_dict=json.loads(file.read())
        except:
            continue
        cur_tf_idf=0
        for term in search_terms:
            if(term in cur_dict):
                cur_tf_idf+=cur_dict[term]*idf[term]
        order.append((filename,cur_tf_idf))
    return order

def crawl():
    html=get_html("docs.python.org","/3/library/concurrency.html")
    https_header,real_html=read_https_header(html)
    text,script,links=parse_html(real_html)
    site='docs.python.org'
    sub='/3/library/concurrency.html'
    for_idf={}
    cnt=0
    file_written=0
    N=500
    while(file_written<N and len(links)>0 and cnt<len(links)):
        cur_link=links[cnt]
        if(cur_link[0]=='.'): 
            cnt+=1
            continue
        if(cur_link[0]=='#'):
            cnt+=1
            continue
        elif (cur_link[0]=='h'):
            cnt+=1
            continue
        else :
            try:
                if(cur_link.find("#")>=0):
                    cnt+=1
                    continue
                index=sub.rfind('/')
                cur_sub=sub.replace(sub[index+1:len(sub)],cur_link)
                file_addr="sites/"+(site+cur_sub).replace('/','_')
                if(os.path.exists(file_addr)): 
                    cnt+=1
                    continue
                text=get_html(site,cur_sub)
                https,html=read_https_header(text)
                text_from_html,scripts,links_dont_need=parse_html(html)
                links+=links_dont_need
                
                file=open(file_addr,"w",encoding="utf-8")
                #file.write(text_from_html)
                term_dict,new_terms=calc_tf(text_from_html)
                for term in new_terms:
                    if term in for_idf:
                        for_idf[term]=for_idf.get(term)+1
                    else: for_idf[term]=1
                file.write(json.dumps(term_dict))
                file.close()
                print("Wrote "+file_addr)
                file_written+=1
                cnt+=1
                continue
            except:
                cnt+=1
                continue
    #print(for_idf)
    for term in for_idf:
        for_idf[term]=math.log10(N/for_idf.get(term))
    f=open("idf","w")
    f.write(json.dumps(for_idf))
    f.close()
        
if __name__=='__main__':
    #crawl()
    res=search("xml")
    res.sort(key=lambda x: x[1],reverse=True)
    print("BEST RESULTS:")
    for i in range(0,10):
        print(str(i+1)+":"+res[i][0].replace("_","/"))
    print("SELECT ONE:")
    val=input()
    args=res[int(val)-1][0].split('_',1)
    content=get_html(args[0],'/'+args[1].replace('_',"/"))
    https,html=read_https_header(content)
    text,ne,netreba=parse_html(html)
    print(text)
    #tf-idf