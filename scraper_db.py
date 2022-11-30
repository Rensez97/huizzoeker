import datetime
import requests
import re
import pickle
import time

from bs4 import BeautifulSoup
from email_func import email_error, email_new, write_msg


# error handling + expceptions
# 1. if there are no houses at pages, skip(but print or email error)(see how to do with if search:)
# 2. if some data on houses cannot be found, skip(but print or email error)
# 3. if value is not what it should be, or should look like(example 90. euro)
# 4. hardcode, stop if more then x amount of verhuurd
# 5. Or hardcode search functions with in websites(pandomo has 177 houses, only little within search reach for optimum speed)

# Search options, min/max price, min/max m2, rooms,


# status = Verhuurd/Beschikbaar
def nova():
    print("Nova vastgoed checken...")
    page = 1
    results = []
    for i in range(30):
        req = requests.get("https://novavastgoed.com/huuraanbod/page/" +
                           str(page)+"/?location=groningen")
        soup = BeautifulSoup(req.text, 'html.parser')
        huizen = soup.find_all("div", {"class": "rh_list_card__wrap"})
        if len(huizen) == 0:
            break
        for huis in huizen:
            try:
                #searching for status on home page for availability and skip iteration if unavailable
                status = huis.find("span", {"class": "property-label"}).text.strip()
                if status != "Beschikbaar":
                    continue
                
                #opening link to house page from search list
                pagina = huis.find('a', href=True)['href']
                req2 = requests.get(pagina)
                huissoup = BeautifulSoup(req2.text, 'html.parser')

                #finding status, price and inclusive in right-top bar
                doublestats = huissoup.find("div", {"class": "rh_page__property_price"})
                kost = doublestats.find("p", {"class": "price"}).text.split()
                prijs = kost[0].strip()
                # clear € and . from int
                prijs = prijs[1:].replace(".", "")
                inc = kost[2].strip()

                #finding type of home and adres in topbar
                breadcrumbs = huissoup.find("nav", {"class": "property-breadcrumbs"})
                typewoning = breadcrumbs.find_all("li")[1].text.strip()
                adres = huissoup.find("p", {"class": "rh_page__property_address"}).text.strip().split(",")[:2] #[nummer/straat,straat/buurt]

                #finding details on m2 and number of rooms
                details = huis.find('div', {"class": "rh_property__row rh_property__meta_wrap"})
                labels = huis.find_all("span", {"class": "figure"})
                opper = eval(labels[-1].text.strip())

                #set numbers of rooms to 1 if not appartement of house
                if typewoning not in ["Studio","Kamer"]:
                    kamers = eval(labels[0].text.strip())
                else:
                    kamers = 0
                results.append([nova.__name__,adres,typewoning,opper,kamers,prijs,inc,status,pagina])
            except Exception as e:
                email_error(nova.__name__, e, huis)
                print("Oeps, iets is misgegaan")
        page += 1
    print("Einde nova vastgoed\n")
    return results


# status = Verhuurd/Nieuw in verhuur/Prijsverlaging
def nulvijf():
    print("050 vastgoed checken...")
    page = 0
    results = []
    for i in range(10):
        req = requests.get("https://050vastgoed.nl/woningaanbod/huur/groningen?locationofinterest=Groningen&moveunavailablelistingstothebottom=true&orderby=8&skip=" +
                           str(page))
        soup = BeautifulSoup(req.text, 'html.parser')
        huizen = soup.find_all("article", {
                               "class": "objectcontainer col-12 col-xs-12 col-sm-6 col-md-6 col-lg-4"})
        if len(huizen) == 0:
            break
        for huis in huizen:
            try:
                #searching for status on home page for availability and skip iteration if unavailable
                status = huis.find("div", {"class": "object_status_container"}).text.strip()
                if status == "Verhuurd":
                    continue

                #finding adres, squared m2, bedrooms, costs and inc on search page
                adres = huis.find("span", {"class": "street"}).text
                sqfeet = huis.find(
                    "span", {"class": "object_label object_sqfeet"})
                if sqfeet:
                    sqfeet2 = sqfeet.find("span", {"class": "number"})
                opper = sqfeet2.text.split()[0]
                opper = opper.replace(",", ".")

                bedrooms = huis.find(
                    "span", {"class": "object_label object_bed_rooms"})
                if bedrooms:
                    kamers = bedrooms.find("span", {"class": "number"}).text
                else:
                    kamers = 0

                kost = huis.find("span", {"class": "obj_price"})
                kostlist = kost.text.strip().split()
                #deleting all numbers beyond the ,
                prijs = kostlist[1].split(",")[0].replace(".", "")
                if len(kostlist) > 3:
                    inc = kostlist[3][:3]
                else:
                    inc = "excl"

                #entering page of house self for type house
                url = huis.find('a', href=True)['href']
                pagina = "https://050vastgoed.nl"+url
                req2 = requests.get(pagina)
                huissoup = BeautifulSoup(req2.text, 'html.parser')
                specs = huissoup.find("div", {"id": "nav-features"})
                for element in specs.find_all('td', text=re.compile("Type object")):
                    typewoning = element.find_next('td').text.split()[0]
                results.append([nulvijf.__name__,adres,typewoning,opper,kamers,prijs,inc,status,pagina])
            except Exception as e:
                #email_error(nulvijf.__name__, e, huis)
                print("Oeps, iets is misgegaan")
        page += 10
    print("Einde 050\n")
    return results


# typewonning not as aspects in page and kamers mentioned different or not at per house
# set standard to exclusive price
# no status possible due to filtering out hired within function, though status is at location if price if unavailable
def solide():
    print("Solide verhuur checken...")
    page = 1
    results = []
    for i in range(5):
        req = requests.get("https://solideverhuur.nl/page/" +
                           str(page)+"/?action=epl_search&post_type=rental&property_location=20")
        soup = BeautifulSoup(req.text, 'html.parser')
        search = soup.find("ul", {"id": "search-results"})
        if search:
            huizen = search.find_all("li", recursive=False)
            for huis in huizen:
                try:
                    #finding active status
                    status = huis.find(
                        "span", {"class": re.compile("status-sticker")}).text.strip()
                    #break loop if house not available
                    if status != "Nieuw":
                        continue
                    adres = huis.find("span", {"class": "street-name"}).text
                    typewoning = "?"

                    # finding square feet
                    specs = huis.find(
                        "ul", {"class": "search-result-specs fa-ul"})
                    opper = huis.find("li").text.split()[0]
                    specslist = huis.find_all("li")
                    c = 0
                    for item in specslist:
                        if "slaapkamer" in item.text:
                            c += 1
                            kamers = item.text.split()[0]
                    if c == 0:
                        kamers = 0
                    
                    # finding costs of house
                    prijs = huis.find(
                        "span", {"class": "page-price"}).text[1:].replace(".", "")
                    inc = "exclusief"
                    # link to page
                    pagina = huis.find('a', href=True)['href']
                    if prijs.isnumeric():
                        results.append([solide.__name__,adres,typewoning,opper,kamers,prijs,inc,status,pagina])
                except Exception as e:
                    email_error(solide.__name__, e, huis)
                    print("Oeps, iets is misgegaan")
            page += 1
    print("Einde solide vastgoed\n")
    return results


# status = Nieuw/Onder optie
def mvgm():
    print("MVGM(ikwilhuren.nu) checken...")
    page = 1
    results = []
    for i in range(10):
        req = requests.get(
            "https://ikwilhuren.nu/huurwoningen/groningen/pagina/"+str(page))
        soup = BeautifulSoup(req.text, 'html.parser')
        search = soup.find("ul", {"id": "search-results"})
        if search:
            huizen = search.find_all("li", recursive=False)
            if len(huizen) == 0:
                break
            for huis in huizen:
                try:
                    #searching for status on home page for availability and skip iteration if unavailable
                    status = huis.find(
                        "span", {"class": re.compile("status-sticker")}).text.strip()
                    if status != "Nieuw":
                        continue

                    #finding adress
                    adres = huis.find("span", {"class": "street-name straat"}).text
                    typewoning = "?"
                    # finding square feet
                    opper = huis.find(
                        "li", {"class": "oppervlakte"}).text[11:].split()[0]
                    kamers = huis.find(
                        "li", {"class": "slaapkamers"}).text[11:].split()[0]
                    # finding costs of house
                    prijs = huis.find(
                        "span", {"class": "page-price"}).text[1:].replace(".", "")
                    inc = "Exclusief"
                    # link to page
                    pagina = huis.find('a', href=True)['href']
                    results.append([mvgm.__name__,adres,typewoning,opper,kamers,prijs,inc,status,pagina])
                except AttributeError:
                    print(
                        "Geen data over object beschikbaar(waarschijnlijk parkeerplaats)")
                except Exception as e:
                    email_error(mvgm.__name__, e, huis)
                    print("Oeps, iets is misgegaan")
        page += 1
    print("Einde MVGM\n")
    return results


# set inc automatic to exclusief
# status = Nieuw/beschikbaar/TE HUUR/onder optie/verhuurd
def pandomo():
    print("Pandomo makelaars checken...")
    page = 1
    results = []
    for i in range(10):
        req = requests.get("https://www.pandomo.nl/huurwoningen/?filter-group-id=10&filter[44][0]=GRONINGEN&page="+str(
            page))
        soup = BeautifulSoup(req.text, 'html.parser')
        search = soup.find("ol", {"class": "results"})
        if search:
            huizen = search.find_all("li", recursive=False)
            for huis in huizen:
                try:
                    #searching for status on home page for availability and skip iteration if unavailable
                    if huis.find("span", {"class": re.compile("results__item__image__label")}):
                        status = huis.find("span", {"class": re.compile(
                            "results__item__image__label")}).text
                    else:
                        status = huis.find("div", {"class": re.compile(
                            "results__item__image__label")}).text
                    if status == "onder optie" or status.lower() == "verhuurd":
                        continue
                    #finding adres
                    adres = huis.find("h3", {"class": "results__item__title"}).text

                    # finding square feet
                    if huis.find("span", {"class": "info__item"}):
                        opper = huis.find(
                            "span", {"class": "info__item"}).text.strip().split()[0]
                    else:
                        opper = 0

                    # finding costs of house
                    if len(huis.find("strong").text.split()) == 3:
                        prijs = huis.find("strong").text[2:-7].replace(".", "")
                    else:
                        prijs = huis.find("strong").text.split()[
                            2][:-3].replace(".", "")
                    inc = "exclusief"

                    # link to page and house detailed object
                    pagina = huis.find('a', href=True, attrs={
                                       'class': None})['href']
                    pagina = "https://www.pandomo.nl"+pagina
                    req2 = requests.get(pagina)
                    huissoup = BeautifulSoup(req2.text, 'html.parser')

                    # find type of house
                    specs = huissoup.find("div", {"class": "spec-box"})
                    for element in specs.find_all('th', text=re.compile("Type Object")):
                        typewoning = element.find_next('td').text.split()[0]

                    # find number of rooms
                    for element in specs.find_all('th', text=re.compile("Kamers")):
                        kamers = element.find_next('td').text.split()[1][1:]
                    results.append([pandomo.__name__,adres,typewoning,opper,kamers,prijs,inc,status,pagina])
                except Exception as e:
                    email_error(pandomo.__name__, e, huis)
                    print("Oeps, iets is misgegaan")
        page += 1
    print("Einde pandomo makelaars\n")
    return results


# status = Beschikbaar/Optie/Verhuurd
def vdmeulen():
    print("Van der Meulen makelaars checken...")
    page = 1
    results = []
    for i in range(10):
        url = "https://www.vandermeulenmakelaars.nl/objecten/page/"+str(page)
        req = requests.get(url)
        soup = BeautifulSoup(req.text, 'html.parser')
        huizen = soup.find_all("article", {
                               "class": "property-listing-simple property-listing-simple-1 hentry clearfix"})
        if huizen:
            for huis in huizen:
                try:
                    #searching for status on home page for availability and skip iteration if unavailable
                    if huis.find("span", {"class": "status"}):
                        status = huis.find(
                            "span", {"class": "status"}).text.strip()
                    else:
                        status = "Beschikbaar"
                    if status != "Beschikbaar":
                        continue

                    #finding adres
                    adres = huis.find("h3", {"class": "entry-title"}).text

                    # finding square feet
                    specs = huis.find_all("span", {"class": "meta-item-value"})
                    opper = specs[0].text[:-2]
                    kamers = specs[1].text
                    # finding costs of house
                    prijs = huis.find(
                        "span", {"class": "price"}).text[1:-2].replace(".", "")

                    #going to detailed page of house
                    pagina = huis.find('a', href=True)['href']
                    req2 = requests.get(pagina)
                    huissoup = BeautifulSoup(req2.text, 'html.parser')

                    #eengezinswoning,bovenwoning,appartement,woning
                    content = huissoup.find("div", {"class": "property-content"}).text
                    if "appartement" in content:
                        typewoning = "Appartement"
                    if "woning" in content:
                        typewoning = "Woning"

                    #search for inclusive or exclusief
                    if "inclusief" in content:
                        inc = "inclusief"
                    if "exclusief" in content:
                        inc = "exclusief"
                    results.append([vdmeulen.__name__,typewoning,opper,kamers,prijs,inc,status,pagina])
                except Exception as e:
                    email_error(vdmeulen.__name__, e, huis)
                    print("Oeps, iets is misgegaan")
        page += 1
    print("Einde van der Meulen makelaars\n")
    return results



# inc not clear, studio's often inclusive though not always
# status = Beschikbaar/In optie/Verhuurd
def eentweedriewonen():
    print("123 wonen checken...")
    page = 1
    results = []
    for i in range(10):
        req = requests.get("https://www.123wonen.nl/huurwoningen/in/groningen/page/" +
                           str(page))
        soup = BeautifulSoup(req.text, 'html.parser')
        search = soup.find("div", {"class": "row pandlist"})
        if search:
            huizen = search.find_all("div", {"class": "pandlist-container"})
            for huis in huizen:
                try:
                    #searching for status on home page for availability and skip iteration if unavailable
                    if huis.find("span", {"class": re.compile("pand-status")}):
                        status = huis.find(
                            "span", {"class": re.compile("pand-status")}).text
                        if status == "Tip":
                            status = "Beschikbaar"
                    else:
                        status = "Beschikbaar"
                    if status != "Beschikbaar":
                        continue
                    # finding the house's adress
                    adres = huis.find("span", {"class": "pand-address"}).text
                    specs = huis.find("div", {"class": "pand-specs"})
                    for element in specs.find_all('span', text=re.compile("Type")):
                        typewoning = element.find_next('span').text
                    for element in specs.find_all('span', text=re.compile("Woonoppervlakte")):
                        opper = element.find_next('span').text.split()[0]
                    for element in specs.find_all('span', text=re.compile("Slaapkamers")):
                        kamers = element.find_next('span').text
                    
                    #finding costs of house
                    prijs = huis.find(
                        "div", {"class": "pand-price"}).text[2:-8].replace(".", "")
                    if typewoning == "Studio":
                        inc = "inclusief"
                    else:
                        inc = "exclusief"

                    # link to page
                    pagina = huis['onclick'][15:-2]
                    results.append([eentweedriewonen.__name__,adres,typewoning,opper,kamers,prijs,inc,status,pagina])
                except Exception as e:
                    #email_error(eentweedriewonen.__name__, e, huis)
                    print("Oeps, iets is misgegaan")
        page += 1
    print("Einde 123 wonen\n")
    return results


# need checking on status 
# status = Nieuw/Verhuurd/(Optie?)
def wbnn():
    print("Woonbemiddeling Noord-Nederland checken...")
    page = 1
    results = []
    for i in range(1):
        req = requests.get(
            "https://wbnn.nl/index.php?searchphrase=Groningen&search=&search-type=rental&p=huizen")
        soup = BeautifulSoup(req.text, 'html.parser')
        huizen = soup.find_all("tr", {"class": "houses-list-row"})
        if huizen:
            for huis in huizen:
                try:
                    adres = huis.find("td", {"data-title": "Locatie"}).text.split()[2]
                    typewoning = huis.find(
                        "td", {"data-title": "Type"}).text
                    # finding square feet
                    opper = huis.find(
                        "td", {"data-title": "Oppervlakte"}).text[:-2]
                    kamers = huis.find(
                        "td", {"data-title": "Aantal kamers"}).text      
                    if int(kamers) == 1:
                        print("l")
                    else:
                        kamers = int(kamers) - 1
                    # finding costs of house
                    prijs = huis.find(
                        "td", {"data-title": "Prijs"}).text[2:-12]
                    inc = huis.find("td", {"data-title": "Prijs"}).text[-7:-2]
                    # finding active status
                    specs = huis.find("td", {"data-title": "Locatie"})
                    status = specs.find("span").text.strip()
                    # link to page
                    site = huis.find("td", {"data-title": "Details"})
                    pagina = site.find("a")['href']
                    pagina = "https://wbnn.nl/"+pagina
                    results.append([wbnn.__name__,adres,typewoning,opper,kamers,prijs,inc,status,pagina])
                except Exception as e:
                    email_error(wbnn.__name__, e, huis)
                    print("Oeps, iets is misgegaan")
        page += 1
    print("Einde Woonbemiddeling Noord-Nederland\n")
    return results


# has 30 items on front page(all new contained in there probably), yet has not mutiple searchable pages
# status = Nieuw/Topper/Bezichtiging/Verhuurd/Verhuurd (onder voorbehoud)
def rotsvast():
    print("Rotsvast vastgoed checken...")
    results = []
    for i in range(1):
        req = requests.get(
            "https://www.rotsvast.nl/woningaanbod/?type=2&city=Groningen&office=0&count=30")
        soup = BeautifulSoup(req.text, 'html.parser')
        huizen = soup.find_all(
            "div", {"class": "residence-gallery clickable-parent col-md-4"})
        if huizen:
            for huis in huizen:
                try:
                    # finding active status
                    status = huis.find(
                        "div", {"class": re.compile("status")}).text
                    if status == "Topper":
                        status = "Nieuw"
                    if status != "Nieuw":
                        continue
                    adres = huis.find("div", {"class": "residence-street"}).text

                    # link to page
                    pagina = huis.find("a")['href']
                    req2 = requests.get(pagina)
                    huissoup = BeautifulSoup(req2.text, 'html.parser')
                    for element in huissoup.find_all('div', text="Soort"):
                        typewoning = element.find_next('div').text.strip()

                    # finding square feet
                    properties = huis.find(
                        "div", {"class": "residence-properties"}).text.split()
                    for element in huissoup.find_all('div', text="Oppervlakte (ca.)"):
                        opper = element.find_next('div').text.strip().split()[0]
                    for element in huissoup.find_all('div', text="Aantal slaapkamers"):
                        kamers = element.find_next('div').text.strip()
                    # finding costs of house
                    totaal = huis.find(
                        "div", {"class": "residence-price"}).text.split()
                    prijs = totaal[1].replace(".", "").replace(",", ".").split(".")[0]
                    inc = totaal[-1]
                    results.append([rotsvast.__name__,adres,typewoning,opper,kamers,prijs,inc,status,pagina])
                except Exception as e:
                    #email_error(rotsvast.__name__, e, huis)
                    print("Oeps, iets is misgegaan")
    print("Einde rotsvast vastgoed\n")
    return results


# only one page
# status = Beschikbaar/Verhuurd/Verhuurd onder voorbehoud
def rec():
    print("Real estate consultancy(REC) checken...")
    results = []
    for i in range(1):
        req = requests.get("https://recvastgoed.nl/huurwoningen/")
        soup = BeautifulSoup(req.text, 'html.parser')
        huizen = soup.find_all(
            "div", {"class": "col-md-4 col-sm-6 huurwoning"})
        if huizen:
            for huis in huizen:
                try:
                    # #finding active status
                    if huis.find("div", {"class": "woning-label"}):
                        status = huis.find(
                            "div", {"class": "woning-label"}).text.strip()
                    else:
                        status = "Beschikbaar"
                    if status != "Beschikbaar":
                        continue
                    # finding costs of house
                    prijs = huis.find("span", {"class": "prijs"}).text[2:].replace(
                        ".", "").replace(",", ".").split(".")[0]
                    inc = "exclusief"

                    # link to page
                    pagina = huis.find("a")['href']
                    req2 = requests.get(pagina)
                    huissoup = BeautifulSoup(req2.text, 'html.parser')
                    # find adres
                    all_content = huissoup.find("div", {"id": "single-woning"})
                    adres = all_content.find("h1").text.split("|")[0]
                    woning_content = huissoup.find("div", {"class": "woning-content"}).text
                    #print(woning_content,adres)
                    if "appartement" in woning_content:
                        typewoning = "Appartement"
                    else:
                        typewoning = "Woning"
                    specs = huissoup.find("div", {"class": "detail-list"})
                    specslist = specs.find("ul")
                    #print(specslist)
                    c = 0
                    for item in specslist:
                        if c == 5:
                            opper = item.text.strip()[:-2]
                        c += 1
                    kamers = specslist.find_all('li')
                    for item in kamers:
                        if "slaapkamers" in item.text:
                            kamers = item.text.split()[0]
                    results.append([rec.__name__,adres,typewoning,opper,kamers,prijs,inc,status,pagina])
                except Exception as e:
                    #email_error(rec.__name__, e, huis)
                    print("Oeps, iets is misgegaan")
    print("Einde Real estate consultancy(REC)\n")
    return results


#[makelaar,adres,typewoning,opper,kamers,prijs,inc,status,pagina]
def gruno():
    print("Gruno checken...")
    page = 1
    results = []
    for i in range(10):
        req = requests.get("https://www.grunoverhuur.nl/huuraanbod/page/" +
                           str(page)+"/?search_property&lang=nl&property_type&property_area&property_bedrooms&property_city=Groningen&price_min=300%2C00&price_max=900%2C00")
        soup = BeautifulSoup(req.text, 'html.parser')
        search = soup.find_all("div", {"class": "gdlr-core-pbf-element"})
        if search:
            huizen = search[4].find_all("div", {"id": re.compile("property")})
            for huis in huizen:
                totaal = huis.find("span", {"class": "price"}).text.strip()
                inc = totaal[-6:-1]
                prijs_list = [char for char in totaal if char.isdigit()][:-2]
                prijs = "".join(prijs_list)
                opper = huis.find(
                    "span", {"title": "Oppervlakte"}).text.strip()[:-2]
                pagina = huis.find("a")['href']
                kamers = huis.find(
                    "span", {"title": "Slaapkamers"})
                if kamers is None:
                    kamers = 1
                else:
                    kamers = kamers.text.strip()
                status = huis.find("div", {"class": re.compile(
                    "rem-sale rem-sale-top-left")})
                if status is None:
                    status = "Beschikbaar"
                else:
                    status = status.text.strip()
                results.append([opper, prijs, "?", pagina])
            page += 1
    print("Einde Gruno\n")
    print(results)
    return results


# function to compare new results to active list of houses and update where needed
def update(oldlist, newlist):
    cnew = 0
    cdel = 0
    for new in newlist:
        new.insert(0, "()")
        # update new status into old if already present
        for old in oldlist:
            if new[1:] == old[1:] and old[0] == "(Nieuw)":
                old[0] = "()"
        # append to list if item is new and mark as new
        if new not in oldlist:
            cnew += 1
            new[0] = "(Nieuw)"
            oldlist.append(new)
    # delete item if not anymore online
    for old in oldlist:
        if old not in newlist:
            cdel += 1
            oldlist.remove(old)
    return oldlist, cnew


def main():

    # set variables for m2(x), price excluded costs(y), price included costs(z)
    x = 35
    y = 850
    z = 950

    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print(time.perf_counter())

    # result = [makelaar,adres,typewoning,opper,kamers,prijs,inc,status,link]

    nova_results = nova()

    nulvijf_results = nulvijf()

    solide_results = solide()

    mvgm_results = mvgm()

    pandomo_results = pandomo()

    vdmeulen_results = vdmeulen()

    eentweedriewonen_results = eentweedriewonen()

    wbnn_results = wbnn()

    rotsvast_results = rotsvast()

    rec_results = rec()

    # print(time.perf_counter())
    # # gruno()

    # print(len(nova_results),len(nulvijf_results),len(solide_results),len(mvgm_results),len(pandomo_results),len(eentweedriewonen_results),len(wbnn_results),len(rotsvast_results))
    # # combine all results from different sites
    all_results = nova_results + nulvijf_results + solide_results + mvgm_results + pandomo_results + vdmeulen_results + eentweedriewonen_results +  wbnn_results + rotsvast_results + rec_results
#     for item in all_results:
#         print(item)
    # all_results = wbnn_results + eentweedriewonen_results + rotsvast_results

    #all_results = "LL"

    # oldlist = [['()', '48', '90.', 'excl', 'https://050vastgoed.nl/woningaanbod/huur/groningen/galenuslaan/24-44?forsaleorrent=1&localityid=23523&locationofinterest=Groningen&moveunavailablelistingstothebottom=true&orderby=8&take=10'],
    #            ['()', '41', '620', 'exlc',
    #             'https://solideverhuur.nl/huurwoningen/groningen/4-eendrachtskade-9726cw/'],
    #            ['(Nieuw)', '62', '700', 'excl', 'https://ikwilhuren.nu/huurwoningen/groningen/55-kajuit-90-t-m-208-en-lijzijde-7-t-m-19/kajuit-141'], ['(Nieuw)', '3', '333', 'excl', 'https://ikwilhuren.nu/huurwoningen/groningen/55-kajuit-90-t-m-208-en-lijzijde-7-t-m-19/kajuit-141']]
    # newlist = [['48', '90.', 'excl', 'https://050vastgoed.nl/woningaanbod/huur/groningen/galenuslaan/24-44?forsaleorrent=1&localityid=23523&locationofinterest=Groningen&moveunavailablelistingstothebottom=true&orderby=8&take=10'],
    #            ['41', '620', 'exlc',
    #                'https://solideverhuur.nl/huurwoningen/groningen/4-eendrachtskade-9726cw/'],
    #            ['62', '700', 'excl', 'https://ikwilhuren.nu/huurwoningen/groningen/55-kajuit-90-t-m-208-en-lijzijde-7-t-m-19/kajuit-141'], ['81', '850', '?', 'https://www.123wonen.nl/huur/groningen/eengezinswoning/grevingaheerd-4459-2']]
    # oldlist2 = [['()', '48', '90.', 'excl', 'https://050vastgoed.nl/woningaanbod/huur/groningen/galenuslaan/24-44?forsaleorrent=1&localityid=23523&locationofinterest=Groningen&moveunavailablelistingstothebottom=true&orderby=8&take=10'], ['()', '41', '620', 'exlc', 'https://solideverhuur.nl/huurwoningen/groningen/4-eendrachtskade-9726cw/']] 
    # test12 = [['wbnn', 'Zuilen', 'Eengezinswoning', '86', 2, '1175', 'excl.', 'Verhuurd', 'https://wbnn.nl/index.php?p=huizen&view=1421'], ['eentweedriewonen', 'Lunettenhof', 'Appartement', '51', '1 ', '1025', 'exclusief', 'Beschikbaar', 'https://www.123wonen.nl/huur/groningen/appartement/lunettenhof-4506-2'], ['eentweedriewonen', 'Briljantstraat', 'Tussenwoning', '131', '4 ', '1175', 'exclusief', 'Beschikbaar', 'https://www.123wonen.nl/huur/groningen/tussenwoning/briljantstraat-4509-2'], ['eentweedriewonen', 'Meeuwerderweg', 'Tussenwoning', '85', '2 ', '1350', 'exclusief', 'Beschikbaar', 'https://www.123wonen.nl/huur/groningen/tussenwoning/meeuwerderweg-4507-2'], ['eentweedriewonen', 'Hora Siccamasingel', 'Appartement', '85', '3 ', '1025', 'exclusief', 'Beschikbaar', 'https://www.123wonen.nl/huur/groningen/appartement/hora+siccamasingel-4500-2'], ['eentweedriewonen', 'Jozef Israëlsstraat', 'Bovenwoning', '120', '3 ', '1250', 'exclusief', 'Beschikbaar', 'https://www.123wonen.nl/huur/groningen/bovenwoning/jozef+isra%c3%ablsstraat-4452-2'], ['eentweedriewonen', 'Kleine Bergstraat', 'Studio', '15', '1 ', '530', 'inclusief', 'Beschikbaar', 'https://www.123wonen.nl/huur/groningen/studio/kleine+bergstraat-3608-2'], ['eentweedriewonen', 'Kleine Bergstraat', 'Studio', '32', '1 ', '835', 'inclusief', 'Beschikbaar', 'https://www.123wonen.nl/huur/groningen/studio/kleine+bergstraat-4270-2'], ['eentweedriewonen', 'Kleine Bergstraat', 'Studio', '18', '1 ', '505', 'inclusief', 'Beschikbaar', 'https://www.123wonen.nl/huur/groningen/studio/kleine+bergstraat-4504-2'], ['eentweedriewonen', 'Leeuwarderstraat', 'Bovenwoning', '95', '2 ', '1250', 'exclusief', 'Beschikbaar', 'https://www.123wonen.nl/huur/groningen/bovenwoning/leeuwarderstraat-4505-2'], ['eentweedriewonen', 'Hoge der A', 'Appartement', '38', '1 ', '840', 'exclusief', 'Beschikbaar', 'https://www.123wonen.nl/huur/groningen/appartement/hoge+der+a-4499-2'], ['eentweedriewonen', 'Helperveste', 'Flat (galerij/portiek)', '80', '2 ', '1300', 'exclusief', 'Beschikbaar', 'https://www.123wonen.nl/huur/groningen/flat+galerij-portiek/helperveste-4501-2'], ['eentweedriewonen', 'Fossemaheerd', 'Studio', '25', '1 ', '750', 'inclusief', 'Beschikbaar', 'https://www.123wonen.nl/huur/groningen/studio/fossemaheerd-4498-2']]
    # # print(all_results)


    personal_list = []
    with open("/home/huizzoeker/full_list.pkl","rb") as f2:
        old_list = pickle.load(f2)
        for item in old_list:
            #print(item[3],type(item[3]),item[5],type(item[5]))
            if int(item[3]) >= 30 and int(item[5]) <= 950:
                personal_list.append(item)
    # personal_list.append(['wbnn', 'Zuilen', 'Eengezinswoning', '94', 2, '1175', 'excl.', 'Verhuurd', 'https://wbnn.nl/index.php?p=huizen&view=1421'])
    c = 0
    with open("/home/huizzoeker/personal_list.pkl", "rb") as f:
        old_personal_list = pickle.load(f)
        for item in personal_list:
            if item not in old_personal_list:
                c += 1
    if c > 0:
        text=write_msg(personal_list)
        email_new(text,c)
        print("Email onderweg)")


    with open("/home/huizzoeker/full_list.pkl", "wb") as f:
        pickle.dump(all_results,f)

    with open("/home/huizzoeker/personal_list.pkl", "wb") as f:
        pickle.dump(personal_list,f)



    # print(time.perf_counter())
#     # load the existing house lists and update to the current situation
#     if all_results:
#         with open("current.pkl", "rb") as f:
#             current = pickle.load(f)
#             uptodate, cnew = update(current, all_results)
#         if cnew > 0:
#             text = write_msg(uptodate)
#             email_new(text, cnew)
#             print("Email is onderweg!")
#         with open("current.pkl", 'wb') as f2:
#             pickle.dump(uptodate, f2)


if __name__ == "__main__":
    main()


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
    # finding square feet
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
    # print(status,opper,prijs,pagina)
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
