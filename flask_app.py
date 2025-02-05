from flask import Flask, render_template, request, jsonify
from flask_cors import CORS, cross_origin
from bs4 import BeautifulSoup as bs
import requests
from urllib.request import urlopen as uReq
import pymongo
from requests import Response
from autoscraper import AutoScraper


app = Flask(__name__)  # initialising the flask app with the name 'app'

a = 3


@app.route('/', methods=['POST', 'GET'])  # route with allowed methods as POST and GET
def index():
    if request.method == 'POST':
        searchString1 = request.form['content']
        searchString = request.form['content'].replace(" ", "")  # obtaining the search string entered in the form
        try:
            dbConn = pymongo.MongoClient("mongodb://localhost:27017/")  # opening a connection to Mongo
            db = dbConn['crawlerDB']  # connecting to the database called crawlerDB
            # reviews = db[searchString].find({}) # searching the collection with the name same as the keyword
            reviews = db[searchString].find()
            # reviews = db[searchString].count_documents({})
            if searchString in db.list_collection_names():
                # if reviews.count_documents() > 0: #if there is a collection with searched keyword and it has records in it
                # if b > 0:
                return render_template('results.html', reviews=reviews)  # show the results to user
            else:
                flipkart_url = "https://www.flipkart.com/search?q=" + searchString  # preparing the URL to search the product on flipkart
                uClient: Response = requests.get(flipkart_url)  # requesting the webpage from the internet
                flipkartPage = uClient.content  # reading the webpage
                uClient.close()  # closing the connection to the web server
                flipkart_html = bs(flipkartPage, "html.parser")  # parsing the webpage as HTML
                bigboxes = flipkart_html.find_all("div", {"class": 'cPHDOP col-12-12'})  # seacrhing for appropriate tag to redirect to the product link
                # bigboxes = flipkart_html.find_all("div", {"class": '_1AtVbE col-12-12'})

                del bigboxes[0:2]  # the first 3 members of the list do not contain relevant information, hence deleting them.
                for box in bigboxes:
                    # box = bigboxes[0] #  taking the first iteration (for demo)
                    #   a=box.find('a')['ASCII_SPACES = {str} ' \n\t\x0c\r'href']

                    productLink = "https://www.flipkart.com" + box.find('a')['href']
                    # productLink = "https://www.flipkart.com" + box.find('a')['href', {'class': '_1fQZEK'}].text
                    # product_link_element = box.find('a', {'class': '_1fQZEK'})
                    # product_link = "https://www.flipkart.com" + product_link_element.get('href', '')

                    # productLink = "https://www.flipkart.com" + box.div.div.div.a['href'] # extracting the actual product link
                    prodRes = requests.get(productLink)  # getting the product page from server
                    # prod_html = bs(prodRes.text, "html.parser")  # parsing the product page as HTML
                    prod_html = bs(prodRes.content, "html.parser")
                    # commentboxes = prod_html.find_all("div", class_="_16PBlm")
                    # product_name = prod_html.find('span', {'class': 'B_NuCI'})
                    # print(product_name)
                    Pro_name = prod_html.find_all('span', {'class': 'VU-ZEz'})[0].text
                    commentboxes = prod_html.find_all("div", {"class": "RcXBOT"})
                    # commentboxes = prod_html.findAll("div", {"class": "_16PBlm"})  #finding the HTML section containing the customer comments

                    table = db[searchString1]  # creating a collection with the same name as search string. Tables and Collections are analogous.
                    # filename = searchString+".csv" #  filename to save the details
                    #  fw = open(filename, "w") # creating a local file to save the details
                    headers = "Product, Customer Name, Rating, Heading, Comment \n"  # providing the heading of the columns
                    # fw.write(headers) # writing first the headers to file
                    reviews = []  # initializing an empty list for reviews
                    #  iterating over the comment section to get the details of customer and their comments

                    for commentbox in commentboxes:
                        try:
                            name = commentbox.div.div.find_all('p', {'class': '_2NsDsF AwS1CA'})[0].text

                        except:
                            name = 'No Name'

                        try:
                            rating = commentbox.div.div.div.div.text

                        except:
                            rating = 'No Rating'

                        try:
                            commentHead = commentbox.div.div.div.p.text
                        except:
                            commentHead = 'No Comment Heading'

                        try:
                            comtag = commentbox.div.div.find_all('div', {'class': ''})
                            custComment = comtag[0].div.text
                        except:
                            custComment = 'No Customer Comment'

                        # fw.write(searchString+","+name.replace(",", ":")+","+rating + "," + commentHead.replace(",", ":") + "," + custComment.replace(",", ":") + "\n")
                        mydict = {"Product": Pro_name, "Name": name, "Rating": rating, "CommentHead": commentHead,"Comment": custComment}  # saving that detail to a dictionary
                        x = table.insert_one(mydict)  # inserting the dictionary containing the review comments to the collection
                        reviews.append(mydict)  # appending the comments to the review list
                return render_template('results.html', reviews=reviews)  # showing the review to the user
        except:
            return 'Server not working please try again after some time(:) '
        # return render_template('results.html')
    else:
        return render_template('index.html')


if __name__ == "__main__":
    app.run(port=8000, debug=True)  # running the app on the local machine on port 8000
