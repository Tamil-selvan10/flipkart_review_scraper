from flask import Flask,request,render_template
from flask_cors import CORS,cross_origin
import requests
from bs4 import BeautifulSoup
import logging
logging.basicConfig(level=logging.INFO,
                    filename='scrapper.log',
                    filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%d-%B-%Y %H:%M:%S')
import csv    
import pymongo                


application=Flask(__name__)
app=application

@app.route('/',methods=['GET'])
@cross_origin()
def home():
    return render_template('index.html')

@app.route('/review',methods=['POST','GET'])
@cross_origin()
def review():
    
    if request.method=='POST':

        try:
            search_string=request.form['content'].replace(" ","")
            flipkart_url=f'https://www.flipkart.com/search?q={search_string}'
            flipkart_res=requests.get(flipkart_url)
            flipkart_html=BeautifulSoup(flipkart_res.content,'html.parser')
            bigboxes=flipkart_html.find_all('div',{'class':'_1AtVbE col-12-12'})
            del bigboxes[:2]
            box=bigboxes[0]

            product_link=box.find_all('a',{'class':'_1fQZEK'})[0].get('href')
            product_url=f'https://www.flipkart.com{product_link}'
            product_res=requests.get(product_url)
            product_html=BeautifulSoup(product_res.content,'html.parser')
            comment_boxes=product_html.find_all('div',{'class':'_16PBlm'})

            review_dict=list()


            for comment_box in comment_boxes:

                # Name
                try:
                    name=comment_box.find_all('p',{'class':'_2sc7ZR _2V5EHH'})[0].text
                except:
                    name=''

                # Place
                try:
                    place=comment_box.find_all('p',{'class':'_2mcZGG'})[0].text
                except:
                    place=''

                # Date
                try:
                    date=comment_box.find_all('p',{'class':'_2sc7ZR'})[1].text

                except:
                    date=''

                
                #Rating
                try:
                    rating=comment_box.find_all('div',{'class':'_3LWZlK _1BLPMq'})[0].text

                except:
                    rating=''


                # Short Comments
                try:
                    short_comments=comment_box.find_all('p',{'class':'_2-N8zT'})[0].text
                except:
                    short_comments=''

                # Long Comments
                try:
                    long_comments=comment_box.find_all('div',{'class':'t-ZTKy'})[0].div.div.text
                except:
                    long_comments=''

                # product
                try:
                    product= product_html.find_all('h1',{'class':'yhB1nd'})[0].text               
                except:
                    product=''
                
                my_dict={'Product':product,
                         'Name':name,
                         'Place':place,
                         'Date':date,
                         'Rating':rating,
                         'Short_comments':short_comments,
                         'Long_comments':long_comments
                         }
                if rating :
                    review_dict.append(my_dict)

            #### 1.Create and load the reviews in the .csv file
            filename=search_string+'.csv'
            headers= list(review_dict[0].keys())
            
            with open(filename,'w',newline='',encoding="utf-8") as file:
                writer=csv.DictWriter(file,fieldnames=headers)
                writer.writeheader()
                writer.writerows(review_dict)

            #### 2.Load the reviews into the mongo db atlas
            client=pymongo.MongoClient('mongodb+srv://etamilselvan2710111996:TS47MongoDB2023@cluster0.sgeazoo.mongodb.net/?retryWrites=true&w=majority')
            db=client['flipkart_web_scrapper_db'] # db name
            review_col=db['flipkart_web_scrapper_coll_name'] # collection name
            review_col.insert_many(review_dict)
            
            #### 3. Display the reviews in the html page
            return render_template('results.html',reviews=review_dict)
        
        except Exception as e:
            logging.info(e)
            return f'something is wrong:{e}'

    else:
        return render_template('index.html')
        


if __name__=='__main__':
    app.run()