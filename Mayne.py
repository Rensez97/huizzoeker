
import requests
from bs4 import BeautifulSoup
import re
from email.message import EmailMessage
import ssl
import smtplib


def nova(s,x,y,z):
    print("Nova vastgoed checken...")
    page = 1
    results = []
    for i in range(30):
        url = "https://novavastgoed.com/huuraanbod/page/"+str(page)+"/?location=groningen"
        req = requests.get(url)
        soup = BeautifulSoup(req.text,'html.parser')
        huizen = soup.find_all("div", {"class": "rh_list_card__wrap"})
        for huis in huizen:
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
            pagina = huis.find('a', href=True)
            if status[0].text == s and int(opper) >= x and int(prijs) <= y and inc == "exclusief":
                result = "Huis gevonden met {} m2 voor €{} {}!  {}".format(opper,prijs,inc,pagina['href'])
                results.append(result)
            if status[0].text == s and int(opper) >= x and int(prijs) <= z and inc == "inclusief":
                result = "Huis gevonden met {} m2 voor €{} {}!  {}".format(opper,prijs,inc,pagina['href'])
                results.append(result)
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
        for huis in huizen:
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
            pagina = huis.find('a', href=True)
            if status.text.strip() == s and float(opper) >= x and float(prijs) <= y and inc == "excl":
                result = "Huis gevonden met {} m2 voor €{} {}!  {}".format(opper,prijs,inc,"https://050vastgoed.nl"+pagina['href'])
                results.append(result)
            if status.text.strip() == s and float(opper) >= x and float(prijs) <= z and inc == "inc":
                result = "Huis gevonden met {} m2 voor €{} {}!  {}".format(opper,prijs,inc,"https://050vastgoed.nl"+pagina['href'])
                results.append(result)
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
                #finding square feet
                specs = huis.find("ul", {"class": "search-result-specs fa-ul"})
                opper = huis.find("li").text.split()[0]
                #finding costs of house
                prijs = huis.find("span", {"class": "page-price"}).text[1:].replace(".","")
                #finding active status
                status = huis.find("span", {"class": re.compile("status-sticker")}).text
                #link to page
                pagina = huis.find('a', href=True)
                if prijs.isnumeric():
                    if int(float(opper)) >= x and int(prijs) <= y:
                        result = "Huis gevonden met {} m2 voor €{}!  {}".format(opper,prijs,pagina['href'])
                        results.append(result)
                #print(status,opper,prijs,pagina['href'])
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
            for huis in huizen:
                #finding square feet
                opper = huis.find("li", {"class": "oppervlakte"}).text[11:].split()[0]
                #finding costs of house
                prijs = huis.find("span", {"class": "page-price"}).text[1:].replace(".","")
                #finding active status
                status = huis.find("span", {"class": re.compile("status-sticker")}).text
                #link to page
                pagina = huis.find('a', href=True)
                if status == s and int(opper) >= x and int(prijs) <= y:
                    result = "Huis gevonden met {} m2 voor €{}!  {}".format(opper,prijs,pagina['href'])
                    results.append(result)
                #print(status,opper,prijs,pagina['href'])
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
                pagina = huis.find('a', href=True, attrs={'class': None})
                pagina = "https://www.pandomo.nl"+pagina['href']
                if status == s and int(opper) >= x and int(prijs) <= y:
                    result = "Huis gevonden met {} m2 voor €{}!  {}".format(opper,prijs,pagina)
                    results.append(result)
                #print(status,opper,prijs,pagina)
        page += 1
    print("Einde pandomo makelaars\n")
    return results


def jaap():
    print("jaap checken...")
    page = 1
    results = []
    for i in range(10):
        url = "https://www.jaap.nl/huurhuizen/groningen/overig+groningen/groningen/p"+str(page)
        req = requests.get(url)
        soup = BeautifulSoup(req.text,'html.parser')
        huizen = soup.find("div", {"class": re.compile("house_result_")})
        if huizen:
            for huis in huizen:
                print(huis)
        page += 1
    print("Einde jaap\n")
    return results

def pararius(s,x,y,z):
    print("Pararius checken...")
    page = 1
    for i in range(10):
        url = "https://www.pararius.nl/huurwoningen/groningen/page-"+str(page)
        req = requests.get(url)
        soup = BeautifulSoup(req.text,'html.parser')
        search = soup.find("ul", {"class": "search-list"})
        print(soup)
        if search:
            huizen = search.find_all("li",{"class": "search-list__item search-list__item--listing"},recursive=False)
            for huis in huizen:
                print(huis)
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
        page += 1
    print("Einde pararius\n")


def gruno(s,x,y,z):
    print("Gruno checken...")
    page = 1
    for i in range(10):
        url = "https://www.grunoverhuur.nl/huuraanbod/page/"+str(page)+"/?search_property&lang=nl&property_type&property_area&property_bedrooms&property_city=Groningen&price_min=300%2C00&price_max=900%2C00"
        req = requests.get(url)
        soup = BeautifulSoup(req.text,'html.parser')
        huizen = soup.find_all("div", {"class": "rh_list_card__wrap"})


def email(results):
    #print(products, new_products, updated_products)
    message = EmailMessage()
    text = "\n".join(results)
    message.set_content(text)
    message['FROM'] = "huizzoeker@outlook.com"
    message['TO'] = ["rensevdzee@hotmail.com"]
    message['SUBJECT'] = "Nieuwe huissaus gevonden"
    context = ssl.create_default_context()
    #set up SMTP server
    with smtplib.SMTP('smtp-mail.outlook.com',587) as smtp:
        smtp.starttls(context=context)
        smtp.login(message['FROM'], "Ludosanders")
        smtp.send_message(message)
        smtp.quit()



def main():
    x = 35
    y = 850
    z = 950

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

    #pararius("Nieuw in verhuur",35,750,850)

    #jaap()

    all_results = mvgm_results + pandomo_results
    #print(all_results)

    if all_results:
        with open("actief.txt","r+") as f:
            actief = f.readlines()
            print(actief)
            for item in all_results:
                if item+"\n" not in actief:
                    f.write(item+"\n")
            print("Email is onderweg!")
            email(all_results)

if __name__ == "__main__":
    main()