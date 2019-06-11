##### LIBRARY IMPORTS
import os
import re
import html2text
import urllib
#### GLOBAL VARIABLES
MODULES = []
URLTXT = ""
PDFSTXT = ""
#### FUNCTIONS
def clear_workspace():
    #### FUNCTIONS TO REMOVE TEMPORARY FILES CREATED
    [os.remove(file) for file in os.listdir('./') if file.endswith('.png')]
    os.remove("temp.pdf")
    os.remove("temp-html.html")

def get_html_data(paperurl,is_first):
    global MODULES
    #### FUNCTION TO CONVERT PDF TO HTML AND THEN RETURN RAWHTML
    os.system("curl {} -s -k --insecure > temp.pdf".format(paperurl))
    os.system("pdftohtml temp.pdf -c -q -s {}".format("-l 1" if is_first else "-f 2"))
    exiter = False
    try:
        with open("temp-html.html","r") as fobj:
            rawhtml = fobj.read()
        clear_workspace()
        return rawhtml
    except:
        print("INVALID PDF : {}".format(paperurl))
        return None

def get_text_data(rawhtml):
    #### FUNCTION TO STRIP TAGS FROM HTML TO LEAVE TEXT CONTENT
    hobj = html2text.HTML2Text()
    hobj.ignore_links = True
    return hobj.handle(rawhtml)

def process_text(text):
    #### FUNCTION TO RETURN UNIQUE WORDS FROM BLOCK OF TEXT
    PUNCTUATION = ["-",".","\n","_",","]
    for punc in PUNCTUATION:
        text = text.replace(punc," ")
    text = re.sub(r"[^\w\s]","",text).upper()
    words = []
    for word in text.split(" "):
        if re.search(r"[0-9]",word) is None and re.search(r"[^A-Z]",word) is None and word not in words:
            words.append(word)
    return list(filter(lambda x : x != "", words))

def get_info(paperurl,board):
    #### FUNCTION TO GET PAPER INFO FROM A PAPER
    acturl = urllib.parse.unquote(paperurl)
    rawhtml = get_html_data(paperurl,True)
    if rawhtml is None: return None
    input_text = get_text_data(rawhtml).upper() + acturl.upper()
    module, sess, year = (None,)*3
    #### SEARCH FOR MODULE
    for mod in MODULES:
        if re.search(r"\b{}\b".format(mod),input_text) is not None:
            module = mod; break
    #### SEARCH FOR SESSION
    for month in ["JANUARY","FEBUARY","OCTOBER","NOVEMBER","DECEMBER"]:
        if re.search(r"\b{}\b".format(month),input_text) is not None:
            sess = "WINTER"; break
    if sess is None: sess = "SUMMER"
    #### SEARCH FOR YEAR
    for date in range(1980,2020):
        if re.search(r"\b{}\b".format(str(date)),input_text) is not None:
            year = date; break
    full_info = [board,module,sess,year]
    if any([x is None for x in full_info]):
        print("INSUFFICIENT INFORMATION ON PAPER : {} {} {} {} {}".format(*full_info,paperurl))
        quit()
    print("{} {} {} {}".format(*full_info))
    return full_info

    
def process_paper(board,paperurl,msurl):
    info = get_info(paperurl,board)
    if info is None: return
    rawhtml = get_html_data(paperurl,False)
    if rawhtml is None: return None
    #### CLEAN UP RAW HTML FOR SEARCHING
    INVALIDS = ["&nbsp;","&nbsp","&#160;","&#160"]
    for inv in INVALIDS:
        rawhtml = rawhtml.replace(inv,"")
    #### FIND ALL MATCHES TO QUESTION STARTS
    MASTER_REGEX = r"(<b>([A-Z]?[0-9]+)[^\s\na-zA-Z\d]*?\.[^\n\d]*?<\/b>)"
    matches = re.findall(MASTER_REGEX,rawhtml) + [("__FEJFIOEF__ROGUE","__ROGUE__FHUERIFGH")]
    #### ONE PASS ALGORITHM TO GET TEXT FROM EACH QUESTION BASED OFF MATCHES
    qtexts = []
    qnums = []
    pagenum = 1
    if len(matches) > 0:
        temp = None
        qindex = 0
        for line in rawhtml.split("\n"):
            if re.search("page([0-9]+)-div",line) is not None:
                pagenum += 1
            if matches[qindex][0] in line:
                if temp is not None: qtexts.append(temp)
                temp = ""
                qindex += 1
                qnums.append(pagenum)
            if temp is not None: temp += "\n" + line
        if temp is not None: qtexts.append(temp)
    if len(qtexts) < 3:
        print("NO QUESTIONS FOUND INVALID PAPER")
        return 
    else:
        print("{} QUESTIONS FOUND".format(len(qnums)))
    qtexts = [process_text(get_text_data(t)) for t in qtexts]
    results = []
    for i in range(len(qtexts)):
        results.append("{}@~{}@~{}@~{}@~{}@~{}@~{}@~{}@~{}\n".format(*info,matches[i][1],qnums[i],paperurl,msurl," ".join(qtexts[i])))
    return results

def lsplit(input,delimiter):
    return list(filter(lambda x: x != "",input.split(delimiter)))

#### ENTRYPOINT
def main():
    global MODULES
    #### OPEN FILES
    with open("data/URLS.txt","r") as urlfile:
        URLTXT = urlfile.read()
    with open("docs/PDFS.txt","r") as pdffile:
        PDFSTXT = pdffile.read()
    #### GET URLS
    sections = lsplit(URLTXT,"--------")
    boarddata = {lsplit(head,"\n")[0]:[(lsplit(head,"\n")[1:][i],lsplit(head,"\n")[1:][i+1]) for i in range(0,len(lsplit(head,"\n")[1:]),2)] for head in sections}
    #### GET MODULES
    sections = lsplit(PDFSTXT,"--------")
    MODULES = []
    for line in sections[0].split("\n")[1:]:
        MODULES += line.split(";")[1:]
    sections = sections[1:]
    #### FILTER PROCESSED PAPERS
    preboarddata = boarddata
    boarddata = {board:[pair for pair in boarddata[board] if pair[0] not in PDFSTXT] for board in boarddata}
    #### PROCESS PAPERS
    questions = []
    for board in boarddata:
        for pair in boarddata[board]:
            res = process_paper(board,pair[0],pair[1])
            if res is not None:
                questions += res
    #### UPDATE THE FILE
    complete_data = {lsplit(head,"\n")[0]:[(lsplit(head,"\n")[1:][i]+"\n") for i in range(0,len(lsplit(head,"\n")[1:]),1)] for head in sections}
    for q in questions:
        complete_data[q.split("@~")[0]].append(q)
    file_template = "--------" + PDFSTXT.split("--------")[1]
    for board in complete_data:
        file_template += "--------{}\n".format(board)
        for record in complete_data[board]:
            file_template += record
    with open("docs/PDFS.txt","w") as pdffile:
        pdffile.write(file_template)
    #### PROCESS FINISHED
    numqs = sum([len(complete_data[b]) for b in complete_data])
    print("{} QUESTIONS AVAILABLE".format(numqs))
    clear_workspace();
    quit()

if __name__ == '__main__' : main()