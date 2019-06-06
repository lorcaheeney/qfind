import os
import re
import html2text
import urllib

def process_text(text):
    text = text.replace("-"," ").replace("."," ").replace("\n"," ").replace("_"," ").replace(","," ")
    text = re.sub(r"[^\w\s]","",text).upper()
    words = []
    for word in text.split(" "):
        if re.search(r"[0-9]",word) is None and re.search(r"[^A-Z]",word) is None and word not in words:
            words.append(word)
    return list(filter(lambda x : x!="", words))

def get_info(paperurl):
    MODULES = ["C1","C2","C3","C4","PH1","PH2","PH4","PH5","M1","S1","CH1","CH2","CH4","CH5","FUNDAMENTALS OF COMPUTER SCIENCE"]
    acurl = urllib.parse.unquote(paperurl)
    os.system("curl {}  -k --insecure > test.pdf".format(paperurl,"test"))
    os.system("pdftohtml test.pdf -c -s -l 1")
    try:
        with open("test-html.html") as fobj:
            data = fobj.read()
    except:return None
    h = html2text.HTML2Text()
    h.ignore_links = True
    text = h.handle(data).upper() + acurl.upper()
    module, sess, year = (None,)*3
    for mod in MODULES:
        if re.search(r"\b{}\b".format(mod),text) is not None:
            module = mod; break
    for month in ["JANUARY","FEBUARY","DECEMBER","NOVEMBER","OCTOBER"]:
        if re.search(r"\b{}\b".format(month),text) is not None:
            sess = "WINTER" ; break
    if sess is None: sess = "SUMMER"
    for lyear in range(1990,2020):
        if re.search(r"\b{}\b".format(str(lyear)),text) is not None:
            year = lyear ; break

    print("{} {} {}".format(module,sess,year))
    if any([x is None for x in (module,sess,year)]):
        print("Insufficient information on paper.")
        quit()
    [os.remove(file) for file in os.listdir('./') if file.endswith('.png')]
    [os.remove(file) for file in os.listdir('./') if file.endswith('.html')]
    [os.remove(file) for file in os.listdir('./') if file.endswith('.pdf')]
    return [module,sess,year]

def load_data(paperurl,msurl):
    with open("docs/WJEC.txt","r") as fobj:
        if paperurl in fobj.read() :
            print("PAPER ALREADY ADDED.")
            return
    info = get_info(paperurl)
    if info is None:
        print("INVALID PDF : {}".format(paperurl))
        return
    os.system("curl {} -k --insecure > {}.pdf".format(paperurl,"test"))
    os.system("pdftohtml test.pdf -c -s -f 2")
    with open("test-html.html") as fobj:
        data = fobj.read()
    data = data.replace("&nbsp;","").replace("&nbsp","").replace("&#160;","").replace("&#160","")
    matchesr = re.findall(r"(>[A-Z]?[0-9]+[\.\"]<)",data) + ["grejgerugherugheiu"]
    matches = []
    [matches.append(item) for item in matchesr if item not in matches]
    print(matches)
    qtexts = []
    qnums = []
    pagenum = 1
    if len(matches) > 0:
        lines = data.split("\n")
        temp = None
        curri = 0
        for l in lines:
            if re.search("page([0-9]+)-div",l) is not None:
                pagenum += 1
            if matches[curri] in l:
                if temp is not None: qtexts.append(temp)
                temp = ""
                curri += 1
                qnums.append(pagenum)
            if temp is not None: temp += "\n" + l
        if temp is not None: qtexts.append(temp)
    [os.remove(file) for file in os.listdir('./') if file.endswith('.png')] 
    [os.remove(file) for file in os.listdir('./') if file.endswith('.html')]
    [os.remove(file) for file in os.listdir('./') if file.endswith('.pdf')]
    if len(qtexts) == 0:
        print("NO QUESTIONS FOUND -- INVALID PAPER")
        return
    else:
        print(len(qtexts)," QUESTIONS FOUND.")
    h = html2text.HTML2Text()
    h.ignore_links = True
    texts = [h.handle(q) for q in qtexts]
    unique = [process_text(t) for t in texts]
    for i in range(len(unique)):
        record = "{}@~{}@~{}@~{}@~{}@~{}@~{}@~{}\n".format(info[0],info[1],info[2],i+1,qnums[i],paperurl,msurl," ".join(unique[i]))
        with open("docs/WJEC.txt","a") as fobj:
            fobj.write(record)

def main():
    with open("load/WJEC.txt","r") as fobj:
        data = fobj.read()
    lines = [d for d  in data.split("\n") if d != ""]
    if len(lines) % 2 != 0:
        print("Every paper must have a markscheme.") ; return
    for i in range(0,len(lines)-1,2):
        load_data(lines[i],lines[i+1])
    print("PROCESS FINISHED.")
    with open("docs/WJEC.txt","r") as fobj:
        ldata = fobj.read()
    llines = [d for d  in ldata.split("\n") if d != ""]
    print("{} QUESTIONS FROM {} PAPERS AVAILABLE.".format(len(llines),len(lines)/2))

if __name__ == '__main__' : main()

