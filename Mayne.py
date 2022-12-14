
import requests
from bs4 import BeautifulSoup
import re
from email.message import EmailMessage
import ssl
import smtplib
import datetime
import pickle


#error handling + expceptions
#1. if there are no houses at pages, skip(but print or email error)(see how to do with if search:)
#2. if some data on houses cannot be found, skip(but print or email error)
#3. if value is not what it should be, or should look like(example 90. euro)
#4. hardcode, stop if more then x amount of verhuurd

def nova(s,x,y,z):
    print("Nova vastgoed checken...")
    page = 1
    results = []
    for i in range(30):
        url = "https://novavastgoed.com/huuraanbod/page/"+str(page)+"/?location=groningen"
        req = requests.get(url)
        soup = BeautifulSoup(req.text,'html.parser')
        huizen = soup.find_all("div", {"class": "rh_list_card__wrap"})
        if len(huizen) == 0:
            break
        for huis in huizen:
            try:
                #finding squared m2
                labels = huis.find_all("span", {"class": "figure"})
                opper = eval(labels[-1].text.strip())
                #finding costs of house
                kost = huis.find_all("p", {"class": "price"})
                prijs = kost[0].text.strip().split()[0]
                inc = kost[0].text.strip().split()[2]
                #clear € and . from int
                prijs = prijs[1:].replace(".","")
                #finding status of house
                status = huis.find_all("span", {"class": "property-label"})
                #link to page
                pagina = huis.find('a', href=True)['href']
                if status[0].text == s and int(opper) >= x and int(prijs) <= y and inc == "exclusief":
                    result = [opper,prijs,inc,pagina]
                    results.append(result)
                if status[0].text == s and int(opper) >= x and int(prijs) <= z and inc == "inclusief":
                    result = [opper,prijs,inc,pagina]
                    results.append(result)
            except:
                email_error(nova.__name__,e,huis)
                print("Oeps, iets is misgegaan")
        page += 1
    print("Einde nova vastgoed\n")
    return results


def nulvijf(s,x,y,z):
    print("050 vastgoed checken...")
    page = 0
    results = []
    for i in range(10):
        url = "https://050vastgoed.nl/woningaanbod/huur/groningen?locationofinterest=Groningen&moveunavailablelistingstothebottom=true&orderby=8&skip="+str(page)
        req = requests.get(url)
        soup = BeautifulSoup(req.text,'html.parser')
        huizen = soup.find_all("article", {"class": "objectcontainer col-12 col-xs-12 col-sm-6 col-md-6 col-lg-4"})
        if len(huizen) == 0:
            break
        for huis in huizen:
            try:
                #finding squared m2
                sqfeet = huis.find("span", {"class": "object_label object_sqfeet"})
                if sqfeet:
                    sqfeet2 = sqfeet.find("span", {"class": "number"})
                opper = sqfeet2.text.split()[0]
                opper = opper.replace(",",".")
                #finding costs of house
                kost = huis.find("span", {"class": "obj_price"})
                kostlist = kost.text.strip().split()
                prijs = kostlist[1]
                prijs = prijs.replace(".","").replace(",",".").replace("-","")
                if len(kostlist) > 3:
                    inc = kostlist[3][:3]
                else:
                    inc = "excl"
                #finding status of house
                status = huis.find("div", {"class": "object_status_container"})
                url = huis.find('a', href=True)['href']
                pagina = "https://050vastgoed.nl"+url
                if status.text.strip() == s and float(opper) >= x and float(prijs) <= y and inc == "excl":
                    result = [opper,prijs,inc,pagina]
                    results.append(result)
                if status.text.strip() == s and float(opper) >= x and float(prijs) <= z and inc == "inc":
                    result = [opper,prijs,inc,pagina]
                    results.append(result)
            except:
                email_error(nulvijf.__name__,e,huis)
                print("Oeps, iets is misgegaan")
        page += 10
    print("Einde 050\n")
    return results


def solide(x,y):
    print("Solide verhuur checken...")
    page = 1
    results = []
    for i in range(5):
        url = "https://solideverhuur.nl/page/"+str(page)+"/?action=epl_search&post_type=rental&property_location=20"
        req = requests.get(url)
        soup = BeautifulSoup(req.text,'html.parser')
        search = soup.find("ul", {"id": "search-results"})
        if search:
            huizen = search.find_all("li",recursive=False)
            for huis in huizen:
                try:
                    #finding square feet
                    specs = huis.find("ul", {"class": "search-result-specs fa-ul"})
                    opper = huis.find("li").text.split()[0]
                    #finding costs of house
                    prijs = huis.find("span", {"class": "page-price"}).text[1:].replace(".","")
                    #finding active status
                    status = huis.find("span", {"class": re.compile("status-sticker")}).text
                    #link to page
                    pagina = huis.find('a', href=True)['href']
                    if prijs.isnumeric():
                        if int(float(opper)) >= x and int(prijs) <= y:
                            result = [opper,prijs,"exlc",pagina]
                            results.append(result)
                except:
                    email_error(solide.__name__,e,huis)
                    print("Oeps, iets is misgegaan")
            page += 1
    print("Einde solide vastgoed\n")
    return results


def mvgm(s,x,y):
    print("MVGM(ikwilhuren.nu) checken...")
    page = 1
    results = []
    for i in range(10):
        url = "https://ikwilhuren.nu/huurwoningen/groningen/pagina/"+str(page)
        req = requests.get(url)
        soup = BeautifulSoup(req.text,'html.parser')
        search = soup.find("ul", {"id": "search-results"})
        if search:
            huizen = search.find_all("li",recursive=False)
            if len(huizen) == 0:
                break            
            for huis in huizen:
                try:
                    #finding square feet
                    opper = huis.find("li", {"class": "oppervlakte"}).text[11:].split()[0]
                    #finding costs of house
                    prijs = huis.find("span", {"class": "page-price"}).text[1:].replace(".","")
                    #finding active status
                    status = huis.find("span", {"class": re.compile("status-sticker")}).text
                    #link to page
                    pagina = huis.find('a', href=True)['href']
                    if status == s and int(opper) >= x and int(prijs) <= y:
                        result = [opper,prijs,"excl",pagina]
                        results.append(result)
                except AttributeError:
                    print("Geen data over object beschikbaar(waarschijnlijk parkeerplaats)")
                except Exception as e:
                    email_error(mvgm.__name__,e,huis)
                    print("Oeps, iets is misgegaan")
        page += 1
    print("Einde MVGM\n")
    return results


def pandomo(s,x,y):
    print("Pandomo makelaars checken...")
    page = 1
    results = []
    for i in range(10):
        url = "https://www.pandomo.nl/huurwoningen/?filter-group-id=10&filter[44][0]=GRONINGEN&page="+str(page)
        req = requests.get(url)
        soup = BeautifulSoup(req.text,'html.parser')
        search = soup.find("ol", {"class": "results"})
        if search:
            huizen = search.find_all("li",recursive=False)
            for huis in huizen:
                try:
                    #finding square feet
                    if huis.find("span", {"class": "info__item"}):
                        opper = huis.find("span", {"class": "info__item"}).text.split()[0]
                    else:
                        opper = 0
                    #finding costs of house
                    if len(huis.find("strong").text.split()) == 3:
                        prijs = huis.find("strong").text[2:-7].replace(".","")
                    else:
                        prijs = huis.find("strong").text.split()[2][:-3].replace(".","")
                    #finding active status
                    if huis.find("span", {"class": re.compile("results__item__image__label")}):
                        status = huis.find("span", {"class": re.compile("results__item__image__label")}).text
                    else:
                        status = huis.find("div", {"class": re.compile("results__item__image__label")}).text
                    #link to page
                    pagina = huis.find('a', href=True, attrs={'class': None})['href']
                    pagina = "https://www.pandomo.nl"+pagina
                    if status == s and int(opper) >= x and int(prijs) <= y:
                        result = [opper,prijs,"excl",pagina]
                        results.append(result)
                except:
                    email_error(pandomo.__name__,e,huis)
                    print("Oeps, iets is misgegaan")
        page += 1
    print("Einde pandomo makelaars\n")
    return results


def vdmeulen(s,x,y):
    print("Van der Meulen makelaars checken...")
    page = 1
    results = []
    for i in range(10):
        url = "https://www.vandermeulenmakelaars.nl/objecten/page/"+str(page)
        req = requests.get(url)
        soup = BeautifulSoup(req.text,'html.parser')
        huizen = soup.find_all("article", {"class": "property-listing-simple property-listing-simple-1 hentry clearfix"})
        if huizen:
            for huis in huizen:
                try:
                    #finding square feet
                    opper = huis.find("span", {"class": "meta-item-value"}).text[:-2]
                    #finding costs of house
                    prijs = huis.find("span", {"class": "price"}).text[1:-2].replace(".","")
                    # #finding active status
                    if huis.find("span", {"class": "status"}):
                        status = huis.find("span", {"class": "status"}).text.strip()
                    else:
                        status = "Beschikbaar"
                    # #link to page
                    pagina = huis.find('a', href=True)['href']
                    if status == s and int(opper) >= x and int(prijs) <= y:
                        result = [opper,prijs,"?",pagina]
                        results.append(result)
                except:
                    email_error(vdmeulen.__name__,e,huis)
                    print("Oeps, iets is misgegaan")
        page += 1
    print("Einde van der Meulen makelaars\n")
    return results


def eentweedriewonen(s,x,y):
    print("123 wonen checken...")
    page = 1
    results = []
    for i in range(10):
        url = "https://www.123wonen.nl/huurwoningen/in/groningen/page/"+str(page)
        req = requests.get(url)
        soup = BeautifulSoup(req.text,'html.parser')
        search = soup.find("div", {"class": "row pandlist"})
        if search:
            huizen = search.find_all("div", {"class": "pandlist-container"})
            for huis in huizen:
                try:
                    #finding square feet
                    opper = huis.find("span", string=re.compile("m²")).text[:-3]
                    # #finding costs of house
                    prijs = huis.find("div", {"class": "pand-price"}).text[2:-8].replace(".","")
                    # #finding active status
                    if huis.find("span", {"class": re.compile("pand-status")}):
                        status = huis.find("span", {"class": re.compile("pand-status")}).text
                        if status == "Tip":
                            status = "Beschikbaar"
                    else:
                        status = "Beschikbaar"
                    #link to page
                    pagina = huis['onclick'][15:-2]
                    if status == s and int(opper) >= x and int(prijs) <= y:
                        result = [opper,prijs,"?",pagina]
                        results.append(result)
                except:
                    email_error(eentweedriewonen.__name__,e,huis)
                    print("Oeps, iets is misgegaan")
        page += 1
    print("Einde 123 wonen\n")
    return results


def wbnn(s,x,y,z):
    print("Woonbemiddeling Noord-Nederland checken...")
    page = 1
    results = []
    for i in range(1):
        url = "https://wbnn.nl/index.php?searchphrase=Groningen&search=&search-type=rental&p=huizen"
        req = requests.get(url)
        soup = BeautifulSoup(req.text,'html.parser')
        huizen = soup.find_all("tr", {"class": "houses-list-row"})
        if huizen:
            for huis in huizen:
                try:
                    #finding square feet
                    opper = huis.find("td", {"data-title": "Oppervlakte"}).text[:-2]
                    #finding costs of house
                    prijs = huis.find("td", {"data-title": "Prijs"}).text[2:-12]
                    inc = huis.find("td", {"data-title": "Prijs"}).text[-7:-2]
                    #finding active status
                    specs = huis.find("td", {"data-title": "Locatie"})
                    status = specs.find("span").text.strip()
                    #link to page
                    site = huis.find("td", {"data-title": "Details"})
                    pagina = site.find("a")['href']
                    pagina = "https://wbnn.nl/"+pagina
                    if status == s and int(opper) >= x and int(prijs) <= y and inc == "excl.":
                        result = [opper,prijs,inc,pagina]
                        results.append(result)
                    if status == s and int(opper) >= x and int(prijs) <= z and inc == "incl.":
                        result = [opper,prijs,inc,pagina]
                        results.append(result)
                except:
                    email_error(wbnn.__name__,e,huis)
                    print("Oeps, iets is misgegaan")
        page += 1
    print("Einde Woonbemiddeling Noord-Nederland\n")
    return results


def rotsvast(s,x,y,z):
    print("Rotsvast vastgoed checken...")
    results = []
    for i in range(1):
        url = "https://www.rotsvast.nl/woningaanbod/?type=2&city=Groningen&office=0&count=30"
        req = requests.get(url)
        soup = BeautifulSoup(req.text,'html.parser')
        huizen = soup.find_all("div", {"class": "residence-gallery clickable-parent col-md-4"})
        if huizen:
            for huis in huizen:
                try:
                    #finding square feet
                    properties = huis.find("div", {"class": "residence-properties"}).text.split()
                    index = properties.index("Woonoppervlakte")
                    opper = properties[index+1]
                    #finding costs of house
                    totaal = huis.find("div", {"class": "residence-price"}).text.split()
                    prijs = totaal[1].replace(".","").replace(",",".")
                    inc = totaal[-1]
                    #finding active status
                    status = huis.find("div", {"class": re.compile("status")}).text
                    if status == "Topper":
                        status = "Nieuw"
                    #link to page
                    pagina = huis.find("a")['href']
                    if status == s and int(opper) >= x and float(prijs) <= y and inc == "excl.":
                        result = [opper,prijs,inc,pagina]
                        results.append(result)
                    if status == s and int(opper) >= x and float(prijs) <= z and inc == "incl.":
                        result = [opper,prijs,inc,pagina]
                        results.append(result)
                except:
                    email_error(rotsvast.__name__,e,huis)
                    print("Oeps, iets is misgegaan")
    print("Einde rotsvast vastgoed\n")
    return results


def rec(s,x,y):
    print("Real estate consultancy(REC) checken...")
    page = 1
    results = []
    for i in range(1):
        #only one page
        url = "https://recvastgoed.nl/huurwoningen/"
        req = requests.get(url)
        soup = BeautifulSoup(req.text,'html.parser')
        huizen = soup.find_all("div", {"class": "col-md-4 col-sm-6 huurwoning"})
        if huizen:
            for huis in huizen:
                try:
                    #finding costs of house
                    prijs = huis.find("span", {"class": "prijs"}).text[2:].replace(".","").replace(",",".")
                    # #finding active status
                    if huis.find("div", {"class": "woning-label"}):
                        status = huis.find("div", {"class": "woning-label"}).text
                    else:
                        status = "Beschikbaar"
                    #link to page
                    pagina = huis.find("a")['href']
                    #opening link to find square feet
                    req2 = requests.get(pagina)
                    huissoup = BeautifulSoup(req2.text,'html.parser')
                    specs = huissoup.find("div", {"class": "detail-list"})
                    specslist = specs.find("ul")
                    c = 0
                    for item in specslist:
                        if c == 5:
                            opper = item.text.strip()[:-2]
                        c += 1
                    if status == s and int(opper) >= x and float(prijs) <= y:
                        result = [opper,prijs,"?",pagina]
                        results.append(result)
                except:
                    email_error(rec.__name__,e,huis)
                    print("Oeps, iets is misgegaan")
        page += 1
    print("Einde Real estate consultancy(REC)\n")
    return results




# def vesteda():
#     print("Vesteda checken...")
#     page = 1
#     results = []
#     for i in range(10):
#         url = "https://www.vesteda.com/nl/woning-zoeken?s=Groningen&sc=woning&priceFrom=500&priceTo=9999&bedRooms=0&unitTypes=2&unitTypes=1&unitTypes=4&radius=20&placeType=1&lng=6.56650161743164&lat=53.2193832397461&sortType=0"
#         req = requests.get(url)
#         soup = BeautifulSoup(req.text,'html.parser')
#         print(soup)
#         search = soup.find("ul", {"class": "o-layout o-layout--gutter-base o-layout--equalheight u-margin-bottom-none o-layout--auto-column-300"})
#         print(search)
#         if search:
#             huizen = search.find_all("li")
#             for huis in huizen:
#                 print(huis)
                #finding square feet
                # if huis.find("span", {"class": "info__item"}):
                #     opper = huis.find("span", {"class": "info__item"}).text.split()[0]
                # else:
                #     opper = 0
                # #finding costs of house
                # if len(huis.find("strong").text.split()) == 3:
                #     prijs = huis.find("strong").text[2:-7].replace(".","")
                # else:
                #     prijs = huis.find("strong").text.split()[2][:-3].replace(".","")
                # #finding active status
                # if huis.find("span", {"class": re.compile("results__item__image__label")}):
                #     status = huis.find("span", {"class": re.compile("results__item__image__label")}).text
                # else:
                #     status = huis.find("div", {"class": re.compile("results__item__image__label")}).text
                # #link to page
                # pagina = huis.find('a', href=True, attrs={'class': None})
                # pagina = "https://www.pandomo.nl"+pagina['href']
                # if status == s and int(opper) >= x and int(prijs) <= y:
                #     result = "Huis gevonden met {} m2 voor {}!  {}".format(opper,prijs,pagina)
                #     results.append(result)
                #print(status,opper,prijs,pagina)
    #     page += 1
    # print("Einde vesteda\n")
    # return results


# def jaap():
#     print("jaap checken...")
#     page = 1
#     results = []
#     for i in range(10):
#         url = "https://www.jaap.nl/huurhuizen/groningen/overig+groningen/groningen/p"+str(page)
#         req = requests.get(url)
#         soup = BeautifulSoup(req.text,'html.parser')
#         huizen = soup.find("div", {"class": re.compile("house_result_")})
#         if huizen:
#             for huis in huizen:
#                 print(huis)
#         page += 1
#     print("Einde jaap\n")
#     return results


# def pararius(s,x,y,z):
#     print("Pararius checken...")
#     page = 1
#     for i in range(10):
#         url = "https://www.pararius.nl/huurwoningen/groningen/page-"+str(page)
#         req = requests.get(url)
#         soup = BeautifulSoup(req.text,'html.parser')
#         search = soup.find("ul", {"class": "search-list"})
#         print(soup)
#         if search:
#             huizen = search.find_all("li",{"class": "search-list__item search-list__item--listing"},recursive=False)
#             for huis in huizen:
#                 print(huis)
            # alert = 0
            # #finding squared m2
            # labels = huis.find_all("span", {"class": "figure"})
            # opper = eval(labels[-1].text.strip())
            # #finding costs of house
            # kost = huis.find_all("p", {"class": "price"})
            # prijs = kost[0].text.strip().split()[0]
            # inc = kost[0].text.strip().split()[2]
            # #clear € and . from int
            # prijs = prijs[1:].replace(".","")
            # #finding status of house
            # status = huis.find_all("span", {"class": "property-label"})
            # if status[0].text == s and int(opper) >= x and int(prijs) <= y and inc == "exclusief":
            #     print(opper,prijs,inc+"HUIS!!!")
            # if status[0].text == s and int(opper) >= x and int(prijs) <= z and inc == "inclusief":
            #     print(opper,prijs,inc+"HUIS!!!")
    #     page += 1
    # print("Einde pararius\n")


# def gruno():
#     print("Gruno checken...")
#     page = 1
#     for i in range(10):
#         url = "https://www.grunoverhuur.nl/huuraanbod/page/"+str(page)+"/?search_property&lang=nl&property_type&property_area&property_bedrooms&property_city=Groningen&price_min=300%2C00&price_max=900%2C00"
#         req = requests.get(url)
#         soup = BeautifulSoup(req.text,'html.parser')
#         huizen = soup.find_all("div", {"class": "property-style-6"})
#         if huizen:
#             for huis in huizen:
#                 print(huis)


#email the error if there has happened something faulty
def email_error(website,error,huis):
    message = EmailMessage()
    message.set_content(str(error)+'\n'+str(huis))
    message['FROM'] = "huizzoeker@outlook.com"
    message['TO'] = ["rensevdzee@hotmail.com"]
    message['SUBJECT'] = "Error bij "+website
    context = ssl.create_default_context()
    #set up SMTP server
    with smtplib.SMTP('smtp-mail.outlook.com',587) as smtp:
        smtp.starttls(context=context)
        smtp.login(message['FROM'], "Ludosanders")
        smtp.send_message(message)
        smtp.quit()


def email(results,alert):
    #print(products, new_products, updated_products)
    message = EmailMessage()
    message.set_content(results)
    message['FROM'] = "huizzoeker@outlook.com"
    message['TO'] = ["rensevdzee@hotmail.com"]
    if alert == 1:
        message['SUBJECT'] = "1 nieuwe osso gevonden"
    if alert > 1:
        message['SUBJECT'] = str(alert)+" nieuwe ossos gevonden"
    context = ssl.create_default_context()
    #set up SMTP server
    with smtplib.SMTP('smtp-mail.outlook.com',587) as smtp:
        smtp.starttls(context=context)
        smtp.login(message['FROM'], "Ludosanders")
        smtp.send_message(message)
        smtp.quit()


#function to compare new results to active list of houses and update where needed
def update(oldlist,newlist):
    cnew = 0
    cdel = 0
    for new in newlist:
        new.insert(0,"()")
        #update new status into old if already present
        for old in oldlist:
            if new[1:] == old[1:] and old[0] == "(Nieuw)":
                old[0] = "()"
        #append to list if item is new and mark as new
        if new not in oldlist:
            cnew += 1
            new[0] = "(Nieuw)"
            oldlist.append(new)
    #delete item if not anymore online
    for old in oldlist:
        if old not in newlist:
            cdel += 1
            oldlist.remove(old)
    return oldlist, cnew


#write the message for the email
def writemsg(uptodate):
    str_list = []
    for item in uptodate:
        if item[0] == "(Nieuw)":
            str_list.append("{}Potentieel huis gevonden met {} m2 voor {} {}!  {}".format(item[0],item[1],item[2],item[3],item[4]))
        else:
            str_list.append("Potentieel huis gevonden met {} m2 voor {} {}!  {}".format(item[1],item[2],item[3],item[4]))
    return "\n".join(str_list)

def main():

    #set variables for m2(x), price excluded costs(y), price included costs(z)
    x = 35
    y = 850
    z = 950
    
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    #input = Verhuurd/Beschikbaar
    nova_results = nova("Beschikbaar",x,y,z)

    #input = Verhuurd/Nieuw in verhuur
    nulvijf_results = nulvijf("Nieuw in verhuur",x,y,z)

    #no input possible due to filtering out hired within function
    solide_results = solide(x,y)

    #input = Nieuw/Onder optie
    mvgm_results = mvgm("Nieuw",x,y)

    #input = beschikbaar/onder optie/verhuurd
    pandomo_results = pandomo("beschikbaar",x,y)

    #input = Beschikbaar/Optie/Verhuurd
    vdmeulen_results = vdmeulen("Beschikbaar",x,y)

    #input = Beschikbaar/In optie/Verhuurd
    eentweedriewonen_results = eentweedriewonen("Beschikbaar",x,y)

    #input = Nieuw/Verhuurd/(Optie?)
    wbnn_results = wbnn("Nieuw",x,y,z)

    # status = Nieuw/Topper/Bezichtiging/Verhuurd/Verhuurd (onder voorbehoud)
    rotsvast_results = rotsvast("Nieuw",x,y,z)

    #input = Beschikbaar/Verhuurd/Verhuurd onder voorbehoud
    rec_results = rec("Beschikbaar",x,y)

    #combine all results from different sites
    all_results = nova_results + nulvijf_results + solide_results + mvgm_results + pandomo_results + vdmeulen_results + eentweedriewonen_results + wbnn_results + rotsvast_results + rec_results
    for item in all_results:
        print(item)


#     oldlist = [['()','48', '90.', 'excl', 'https://050vastgoed.nl/woningaanbod/huur/groningen/galenuslaan/24-44?forsaleorrent=1&localityid=23523&locationofinterest=Groningen&moveunavailablelistingstothebottom=true&orderby=8&take=10'],
# ['()','41', '620', 'exlc', 'https://solideverhuur.nl/huurwoningen/groningen/4-eendrachtskade-9726cw/'],
# ['(Nieuw)','62', '700', 'excl', 'https://ikwilhuren.nu/huurwoningen/groningen/55-kajuit-90-t-m-208-en-lijzijde-7-t-m-19/kajuit-141'],['(Nieuw)','3', '333', 'excl', 'https://ikwilhuren.nu/huurwoningen/groningen/55-kajuit-90-t-m-208-en-lijzijde-7-t-m-19/kajuit-141']]
#     newlist = [['48', '90.', 'excl', 'https://050vastgoed.nl/woningaanbod/huur/groningen/galenuslaan/24-44?forsaleorrent=1&localityid=23523&locationofinterest=Groningen&moveunavailablelistingstothebottom=true&orderby=8&take=10'],
# ['41', '620', 'exlc', 'https://solideverhuur.nl/huurwoningen/groningen/4-eendrachtskade-9726cw/'],
# ['62', '700', 'excl', 'https://ikwilhuren.nu/huurwoningen/groningen/55-kajuit-90-t-m-208-en-lijzijde-7-t-m-19/kajuit-141'],['81', '850', '?', 'https://www.123wonen.nl/huur/groningen/eengezinswoning/grevingaheerd-4459-2']]

    #load the existing house lists and update to the current situation
    if all_results:
        with open("/home/huizzoeker/current.pkl", "rb") as f:
            current = pickle.load(f)
            uptodate,cnew = update(current,all_results)
        if cnew > 0:
            text = writemsg(uptodate)
            email(text,cnew)
            print("Email is onderweg!")
        with open("/home/huizzoeker/current.pkl",'wb') as f2:
            pickle.dump(uptodate,f2)

if __name__ == "__main__":
    main()