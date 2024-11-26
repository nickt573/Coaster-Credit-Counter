from bs4 import BeautifulSoup
import requests, re

# Main function, takes in ride and park
def find_page(ride, park):

    ride = ride.strip()
    park = park.strip()
   
    start = park.find('(')
    end = park.find(')')

    if start != -1 and end != -1:
        location = park[start + 1:end].strip() 
        park = park[:start].strip() 
    else:
        location = ""


    results = [] # Main list that contains all information to be returned and later parsed.  Structure should include commentary and http links

    plant = False

    # Quick fix for any user confusion
    # Park corrections
    if park.lower() == "nickelodeon universe american dream" or park.lower() == "american dream":
        park = "Nickelodeon Universe Theme Park"
    if park.lower() == "marineland" or park.lower() == "marine land":
        park = "Marineland Theme Park"
    if park.lower() == "universal studios orlando":
        park = "Universal Studios Florida"
    if "hollywood studios" in park.lower():
        park = "Disney's Hollywood Studios"
   
    # Park planting fixes
    if park.lower() == "holiday world" and location == "":
        plant = True
        park = "https://rcdb.com/4554.htm"
    
    # Ensures no blank input strings and configures the arguments for analysis
    if park == "":
        park = "?"
    else:
        park = park.replace("'", "").replace(" ", "_").lower()
    if ride == "":
        ride = "?"
    else: ride = ride.lower()
    if ride == "?" and park == "?":
        results.append("Please enter a ride or a park")
        return results

    # Branches to search-by-park or search-by-name respectively
    if ride == "?" and park != "?":
        results.extend(list_park_rides(park, location)) # Returns all rides from the park
        return results
    if ride != "?" and park == "?":
        results.extend(find_by_name(ride)) # Returns all rides of that name (or previously that name)
        return results

    # Branches to main search for ride and park together
    try:
        # Begins by searching for the park's main page
        # Checks for a plant
        if plant == False:
            url = f'https://rcdb.com/qs.htm?qs={park}' 
        else: 
            url = park
        while True:  #Ensures search leads to park page
            response = requests.get(url, verify=True)
            response.raise_for_status()
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            
            h4 = soup.find_all('h4') # Checks if link redirects to a list of parks instead of the proper main park
            if len(h4) > 0: # Since rides are put in h4s, an h4 length of 0 means no rides shown
                break
            else:
                sections = soup.find_all('section')
                if not sections:
                    results.append("Could not find park")
                    return results
                for section in sections:
                    if section.find('h3') and "Amusement Park" in section.find('h3').text:
                        ps = section.find_all('p')
                        for p in ps:
                            if "Too many" in p:
                                results.append("Too many parks with that name. Please search by coaster.")
                                return results
                            try:
                                if park.replace("_", " ").lower() in p.find('a').text.lower():
                                    url = "https://rcdb.com" + p.find('a').get('href')
                                    break
                            except Exception as e:
                                results.append("Could not find park")
                                return results
                        else:
                            results.append("Could not find park")
                            return results
                        break
                if results == []:
                    results.append("Could not find park")
                    return results
            
        div_list = soup.find_all('div', class_='stdtbl ctr') # Iterates through all of the ride names 
        for div in div_list:
            a_list = div.find_all('a')
            for a in a_list:
                # *Shrug*
                if ride.replace(":", "").replace("'", "").replace("-", "").replace(" ", "") in a.text.lower().replace(":", "").replace("'", "").replace("-", "").replace(" ", "")   and "/g" not in a.get('href'):
                    results.append("https://rcdb.com" + a.get('href'))          
        if results:
            return results
        results.append("No coaster found")
        return results

    except Exception as e:
        results.append(f"Error: {e}")
        return results
    
# Called if ride input is ?.  Designed to return all coasters at a park
def list_park_rides(park, location):
    data = []
    try:
        #Gathering main park page
        if "https://" not in park:
            url = f'https://rcdb.com/qs.htm?qs={park}'
        else:
            url = park
        while True:  # Ensures search leads to park page
            response = requests.get(url, verify=True)
            response.raise_for_status()
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            
            h4 = soup.find_all('h4')
            if len(h4) > 0: # Checks if link redirects to a list of parks
                break
            else:
                skip = False
                sections = soup.find_all('section')
                if not sections:
                    data.append("Could not find park")
                    return data
                for section in sections:
                    if section.find('h3') and "Amusement Park" in section.find('h3').text:
                        ps = section.find_all('p')
                        for p in ps:
                            if "Too many" in p.text:
                                data.append("Too many parks with that name. Please search by coaster.")
                                return data
                            try: # Location support
                                a_list = p.find_all('a')
                                option = ''
                                for i in a_list:
                                    option += " " + i.text
                                my_park = (park + " " + location).replace("_", " ").replace("-", "").replace("'", "").lower().strip()
                                my_option = option.replace("-", "").replace("'", "").lower()
                                if all(word in my_option for word in my_park.split()) and not skip:
                                    url = "https://rcdb.com" + a_list[0].get('href')
                                    skip = True
                                    break
                            except Exception as e:
                                data.append("Could not find park")
                                return data      
                else:
                    if not skip:
                        data.append("Could not find park")
                        return data

        # Going through all types (operating, defunct, etc) of listed coasters
        for i in range(len(h4)):
            url_o = "https://rcdb.com" + h4[i].find('a').get('href')
            response_o = requests.get(url_o, verify=True)
            response_o.raise_for_status()
            html_o = response_o.text
            soup_o = BeautifulSoup(html_o, 'html.parser')
           
            main_table = soup_o.find('div', class_='stdtbl rer')
            body = main_table.find('tbody')
            tr_list = body.find_all('tr')
            for j in range(0, len(tr_list)):
                td = tr_list[j].find_all('td')
                a = td[1].find('a')

                if a.text in "unknown":
                    # data.append("Unknown coaster") No longer printing unknowns
                    continue
                link = "https://rcdb.com" + a.get('href')
                data.append(link)       
        return data
        
    except Exception as e:
        data.append("Could not find park")
        return data
    
# Returns a ride's height, speed, and # of inversions if possible. Also returns 
# a stats string for extra info if needed in the future
def get_stats(url): 

    # Calculate the datetime representing an appropriate time to update database.
    response = requests.get(url, verify=True)            
    response.raise_for_status()
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    stat_table = soup.find('table', class_='stat-tbl')
    if stat_table is not None:
        trs = stat_table.find_all('tr')
        stats = trs[0].text.split(" ") 
    else:
        stats = {}   

    # Initializing variables
    height = None
    drop = None
    height_2 = None
    drop_2 = None
    dueling = False
    elevation = 0

    for i, data in enumerate(stats):
        if "Name" in stats[0]: # Due to the nature of RCDB, this will reveal dueling coasters
            dueling = True
        if "Height" in data and height == None:
            height = ''.join(filter(lambda x: x.isdigit() or x == '.', data.split("Height")[1]))
            if dueling:
                height_2 = ''.join(filter(lambda x: x.isdigit() or x == '.', stats[i+1]))
        if "Elevation" in data and elevation == 0:
            elevation = data.split("Elevation")[1]
        if "Drop" in data and drop == None: 
            drop = ''.join(filter(lambda x: x.isdigit() or x == '.', data.split("Drop")[1]))
            if dueling:
                drop_2 = ''.join(filter(lambda x: x.isdigit() or x == '.', stats[i+1]))
        if "Speed" in data:
            speed = ''.join(filter(lambda x: x.isdigit() or x == '.', data.split("Speed")[1]))
            if dueling:
                speed_2 = ''.join(filter(lambda x: x.isdigit() or x == '.', stats[i+1]))
                if speed != speed_2:
                    speed = f'{speed}mph/{speed_2}'
            speed = f'{speed}mph'
        if "Inversions" in data:
            pattern = r'Inversions(\d+)'
            match = re.search(pattern, data, re.IGNORECASE)   
            inversions = match.group(1)
            if dueling or inversions == "00": # Fixes same number or different number issues 
                if len(inversions) == len(set(inversions)): # Unique numbers, adds / (See BR Chiller)
                    inversions = '/'.join(inversions)
                else: # Non-unique, 
                    inversions = ''.join(set(inversions))

    # Sorts height/drop/elevation
    if (height is None or height == "") and (drop is None or drop == ""):
        height = "?"
    elif height is None or height == "":
        height = f'{float(drop)}ft'
    elif drop is None or drop == "":
        height = f'{float(height)}ft'
    else:
        try:
            height = f'{max(float(height), float(drop))}ft'
        except:
            height = f'{float(height)}ft'
    try:
        if float(elevation) > float(height.replace("ft", "")):
            height = f'{elevation}ft'
    except:
        pass

    # Dueling height/drop sort
    if height != "?":
        if (height_2 is None or height_2 == "") and (drop_2 is None or drop_2 == ""):
            pass
        elif height_2 is None:
            if height != f'{float(drop_2)}ft':
                height += f'/{float(drop_2)}ft'
        elif drop_2 is None:
            pass
        else:
            try:
                height_2 = f'{max(float(height_2), float(drop_2))}ft'
                if height != height_2:
                    height += "/" + height_2
            except:
                height_2 = f'{float(height_2)}ft'
                if height != height_2:
                    height += "/" + height_2
                

    speed = speed if "speed" in locals() else "?"
    inversions = inversions if "inversions" in locals() else "?"


    # Make:
    make = "Multiple manufactuers or unknown"
    try:
        make_div = soup.find('div', class_='scroll')
        make = make_div.find('a').text.replace("GmbH", "").replace("Manufacturing", "").replace("Co., Ltd.", "").strip()
    except:
        try: 
            tables = soup.find_all('table', class_='stat-tbl')
            for table in tables:
                trs = table.find_all('tr')
                for tr in trs:
                    if 'Designer' in tr.find('th').text:
                        a_list = tr.find_all('a')
                        if len(a_list) == 1:
                            make = a_list[0].text
                        else:
                            raise Exception()
        except:
            pass 
    if make == "Mack Rides  & Co KG":
        make = "Mack Rides"

    # Park:
    try:
        feature_div = soup.find('div', id='feature')
        name = feature_div.find('h1').text
        if "/" in name:
            name = name.split('/')[0].strip()

    except:
        name = "Unknown"
    try:
        park = feature_div.find('a').text
    except:
        park = "Unknown"

    # Status
    try:
        p = feature_div.find('p')
        status = p.find('a').text
        if status == "Operated":
            status = "Defunct"
    except:
        status = "Unknown"


    return height, speed, inversions, make, name, park, status #Could also return stats which can be used for more info

# Returns all rides of ride name
def find_by_name(ride):
    url = f"https://rcdb.com/r.htm?ot=2&ne={ride}"
    i = 1
    data = []
    initial = True

    while initial:
        try:
            response = requests.get(url, verify=True)
            response.raise_for_status()
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            
            if ''.join(filter(str.isdigit, soup.find('table', class_='t-list t-top').find_all('tr')[1].find_all('td')[1].text)) == "0":  
                initial = False
                break
        except:
            if data:
                return data
            else:
                initial = False
                break
            
        main_table = soup.find('div', class_='stdtbl rer')
        body = main_table.find('tbody')
        tr_list = body.find_all('tr')
        for j in range(0, len(tr_list)):
            td = tr_list[j].find_all('td')
            a = td[1].find('a')
            if a: 
                url = "https://rcdb.com" + a.get('href')
                data.append(url)
        i += 1
        url = f"https://rcdb.com/r.htm?page={i}&ot=2&ne={ride}" 

    if not initial:
        if '&' in ride:
            ride = ride.replace('&', '%26')
        url = f'https://rcdb.com/qs.htm?qs={ride}'
        if '%26' in ride:
            ride = ride.replace('%26', '&')
        response = requests.get(url, verify=True)
        response.raise_for_status()
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        sections = soup.find_all('section')
        if not sections:
            data.append("Could not find ride ")
            return data
        for section in sections:
            if section.find('h3') and "Roller Coaster" in section.find('h3').text:
                ps = section.find_all('p')
                for p in ps:
                    if "Too many" in p.text:
                        data.append("Could not find ride - Critical Error")
                        return data
                    try:
                        if ride.replace("_", " ").replace("-", "").replace("'", "").lower() in p.find('a').text.replace("-", "").replace("'", "").lower():
                            url = "https://rcdb.com" + p.find('a').get('href')
                            data.append(url)
                    except Exception as e:
                        data.append("Error loading ride")
                        return data
        if data == []:
            data.append("Could not find ride")
        return data
    else:
        data.append("Could not find ride")   
        return data

# Alternative way of finding ride and park by searching for the ride first
# instead of the park first
def find_park_by_ride(ride, park):
    url = f"https://rcdb.com/r.htm?ot=2&ne={ride}"
    i = 1
    data = []

    start = park.find('(')
    end = park.find(')')

    if start != -1 and end != -1:
        park = park[:start].strip() 

    while True:
        try:
            response = requests.get(url, verify=True)
            response.raise_for_status()
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            
            if ''.join(filter(str.isdigit, soup.find('table', class_='t-list t-top').find_all('tr')[1].find_all('td')[1].text)) == "0":  
                data.append("Could not find ride")
                return data
        except:
            if data:
                return data
            else:
                data.append("Could not find ride")
                return data
            
        main_table = soup.find('div', class_='stdtbl rer')
        body = main_table.find('tbody')
        tr_list = body.find_all('tr')
        for j in range(0, len(tr_list)):
            td = tr_list[j].find_all('td')
            a = td[1].find('a')
            if a and park.replace(" ", "") in td[2].find('a').text.replace("'", "").replace(" ", "").lower(): 
                url = "https://rcdb.com" + a.get('href')
                data.append(url)
        i += 1
        url = f"https://rcdb.com/r.htm?page={i}&ot=2&ne={ride}" 

def main():
    ride = input("Ride: ")
    park = input("Park: ")
    results = find_page(ride, park)
    print()
    for entry in results:
        if "https://" in entry:
            height, speed, inversions, make, name, park, status = get_stats(entry)
            print(f'''{name} - {park}
Height: {height}
Speed: {speed}
Inversions: {inversions}
Manufacturer: {make}
Status: {status}
RCDB Link: {entry}
''')
        else:
            print(entry)

main()