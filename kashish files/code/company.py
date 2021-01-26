#code to extracts Twitter Handles of S&P 500 Companies using selenium script by initiating a google search and then check for their verification by twint lookup.

from selenium import webdriver #used to automate web browser interaction from Python.
from bs4 import BeautifulSoup #pulling data out of HTML and XML files.
import csv
import time
import pandas as pd #open source data analysis / manipulation tool
import twint #Twint is an advanced Twitter scraping tool written in Python that allows for scraping Tweets from Twitter profiles without using Twitter's API.
import nest_asyncio #resolves RunTimeError in twint
nest_asyncio.apply()

CHROMEDRIVER_PATH = r"C:\Users\Harshvardhan\PycharmProjects\chromedriver.exe"

#Variable to store input file name and path
INPUT_PATH = r'C:\Users\Harshvardhan\PycharmProjects\myPython\S&P 500 CEOs post 2007.csv'
INPUT_FILE = 'S&P 500 CEOs post 2007.csv'

#Variable to store Output file name and path
OUTPUT_PATH = r'C:\Users\Harshvardhan\PycharmProjects\myPython\Final_Company_Verified.csv'
OUTPUT_FILE = 'Final_Company_Verified.csv'

#Variable to store file name and path for our main working file which is obtained by dropping duplicates from input file
WORK_PATH = r'C:\Users\Harshvardhan\PycharmProjects\myPython\Company_Exhaustive_List.csv'
WORK_FILE = 'Company_Exhaustive_List.csv'

#Variable to store file name and path which will contain Twint Lookup results
TWINT_PATH = r'C:\Users\Harshvardhan\PycharmProjects\myPython\Company_Lookup.csv'
TWINT_FILE = 'Company_Lookup.csv'

#Function to remove repeated company names and store result in a separate file
def DropDuplicates():
    df = pd.read_csv(INPUT_PATH)
    df = df.drop_duplicates(subset='Company')
    df.to_csv(WORK_FILE, index=False)

#Trimming company names so as to enhance search results
def TrimInput():
    df = pd.read_csv(WORK_PATH)
    df.Company = df.Company.astype(str)

    #Storing company names as list
    company = df.Company.to_list()

    #List to store trimmed company names
    tr_company = []

    #Making required changes by string operations
    for c in company:
         c = c.replace(' CORP', '')
         c = c.replace(' INC', '')
         c = c.replace(' CO', '')
         c = c.replace(' LTD', '')
         c = c.lstrip()
         c = c.lower()
         tr_company.append(c)

    #Creating a new column and saving the edited names
    df["trimmed_company_name"] = tr_company
    df.to_csv(WORK_FILE, index=False)

#Function to Extract Company Handles by initiating a web search
def GoogleSearch():
    #Configuring webdriver to use Chrome browser by setting up the path to chromedriver
    driver = webdriver.Chrome(CHROMEDRIVER_PATH)

    #List to store data scraped from website
    handle = []

    #Opening file
    with open(WORK_PATH, 'r') as file:
        reader = csv.reader(file)
        x = 1

        # iterating through every row
        for row in reader:
            # Opening url
            driver.get("https://duckduckgo.com/")

            # Finding the search box
            element = driver.find_element_by_name("q")

            company_name = row[5]

            search_query = "Twitter: " + company_name

            # Skip header
            if x == 1:
                x = x + 1
                continue

            # sending query to search box
            element.send_keys(search_query)
            element.submit()

            # obtaining url and page content of search results
            url = driver.current_url
            driver.get(url)
            content = driver.page_source

            soup = BeautifulSoup(content, 'lxml')

            # finding html tag in which data is nested to extracting it
            src = soup.find_all("span", {"class": "result__url__domain"})

            try:
                #reading only first value of src
                a = src[0].get_text()

                # if first search result link is twitter site then account exists else doesn't
                if a == "https://twitter.com":
                    # Obtaining Twitter handle from first twitter link
                    src1 = soup.find_all("span", {"class": "result__url__full"})
                    try:
                        result = src1[0].get_text()
                        result = result[1:]#trimming word
                    except IndexError:
                        result = ""
                else:
                    result = ""

                print(result)

                handle.append(result)

                #Sending to sleep because-
                #1.Gives web page to load its content
                #2.Imitates a human kind behaviour. Prevent 'Not a Robot-Captcha'
                time.sleep(10)

            except IndexError:
                #This error will only occur if code trying to extract data before web-page is loaded
                #Increase sleep time to avoid this exception
                #Saving extracted data to a temporary file and breaking from the loop
                print("Error")
                df_temp = pd.DataFrame({'Company_Handles': handle})
                df_temp.to_csv('temp.csv', index=False)
                break #If we donot break the loop would continue giving IndexError

    #reading and appending handles list to csv
    df = pd.read_csv(WORK_PATH)
    df["Company_Handles"] = handle

    #polishing the extracted handles by removing unnecssary characters
    df.Company_Handles = df.Company_Handles.astype(str)
    df = df[~df['Company_Handles'].str.contains('status')]
    df['Company_Handles'] = df['Company_Handles'].str.replace('@', '')
    df['Company_Handles'] = df['Company_Handles'].str.replace('/', '')
    df['Company_Handles'] = df['Company_Handles'].str.replace('nan', '')

    #saving csv file
    df.to_csv(WORK_FILE, index=False)

#Function to run twint lookup on extracted handles
def Twint():
    #opening file
    with open(WORK_PATH, 'r') as file:
        reader = csv.reader(file)
        x = 1

        #iterating through every row
        for row in reader:
            # Skip header
            if x == 1:
                x = x + 1
                continue

            company_handle = row[6]

            #skip empty cell
            if company_handle == '':
                continue

            print(row[6])

            c = twint.Config()
            c.Username = row[6]

            #setting output file name
            c.Output = TWINT_FILE
            c.Store_csv = True
            try:
                #Running Twint Lookup
                twint.run.Lookup(c)
                time.sleep(5)
            except KeyError:
                print("KeyError")
                continue
            except ValueError:
                print("ValueError")
                continue
            except:
                print("Some other error")
                continue
            print("Process ended!")

#Function to merge WORK_FILE and TWINT_FILE to OUTPUT_FILE
def Merge():
    #before merging creating a common column in both files
    #common column is comprised of username in lowercase
    #name of column is small_username

    #reading and adding small_username to WORK_FILE
    df1 = pd.read_csv(WORK_PATH)
    df1.Company_Handles = df1.Company_Handles.astype(str)
    un = df1.Company_Handles.to_list()
    small_un = []
    for u in un:
           u = u.lower()
           small_un.append(u)
    df1["small_username"] = small_un
    df1['Company_Handles'] = df1['Company_Handles'].str.replace('nan', '')
    df1['small_username'] = df1['small_username'].str.replace('nan', '')
    df1.to_csv(WORK_FILE, index=False)

    #reading and adding small_username to TWINT_FILE
    df2 = pd.read_csv(TWINT_PATH)
    df2.username = df2.username.astype(str)
    un = df2.username.to_list()
    small_un = []
    for u in un:
        u = u.lower()
        small_un.append(u)
    df2["small_username"] = small_un
    df2.to_csv(TWINT_FILE, index=False)

    #merging two csv on small_username and saving it to OUTPUT_FILE
    df_merge = pd.merge(df1, df2, how='left', on='small_username')
    df_merge.to_csv(WORK_FILE, index=False)

#Function to obtain only verified handles
def ExtractVerified():
    df = pd.read_csv(WORK_PATH)
    df = df[~(df['verified'] != True)]
    df.to_csv(OUTPUT_FILE, index=False)

#Calling functions
DropDuplicates()
TrimInput()
#Before calling further functions-
#Companies having single word as name (eg- apple, hess, beam) require the extra words. Hence, such company names are changed back to original manually to improve search results.
GoogleSearch()
Twint()
Merge()
#Before calling further functions-
#Manually check handles extracted by GoogleSearch() but threw a KeyError exception in twint.

ExtractVerified()