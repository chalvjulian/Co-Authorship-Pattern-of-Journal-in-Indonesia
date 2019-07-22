from flask import Flask, render_template, request
from flask_mysqldb import MySQL
from flask_table import Table, Col
import pandas as pd
from tqdm import tqdm
import operator
import re

app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'data'
mysql = MySQL(app)

awal, akhir = 1990, 2015

def highlight(pattern, text):
	search = rf"(?i)(?:{pattern})"
	matched_str = re.search(search, text)
	if matched_str:
		text = re.sub(matched_str.group(0), f"<span class='highlight'>{matched_str.group(0)}</span>", text)
	return text

def ngitung_author(jumlah, df):
  tmp = []
  for tahun in tqdm(range(awal, akhir)):
    cnt = 0
    article_id = df[(df.year == str(tahun))].c_article_id
    for id in set(article_id):
      if len([n for n in article_id if n == id]) == jumlah or (len([n for n in article_id if n == id]) >= jumlah and jumlah == 6):
        cnt += 1
    tmp.append(cnt)
  return tmp

@app.route('/', methods=["GET", "POST"])
def home():
	return render_template("home.html")

@app.route('/jurnal', methods=["GET", "POST"])
def jurnal():
	cur = mysql.connection.cursor()
	search_pattern = ""
	start_year = awal
	end_year = akhir

	if request.method == "POST":
		search_pattern = request.form['search_pattern'] or ""
		start_year = request.form['start_year'] or 1990
		end_year = request.form['end_year'] or 2015

	cur.execute(f'SELECT c_article_id, year, author, jurnal, affiliate from tabel_data WHERE c_article_id in (SELECT c_article_id from tabel_data WHERE year BETWEEN {start_year} and {end_year} and jurnal LIKE "%{search_pattern}%")')
	rows = cur.fetchall()
	cur.execute(f'SELECT c_article_id, year, author, jurnal, affiliate from tabel_data WHERE c_article_id in (SELECT c_article_id from tabel_data WHERE year BETWEEN {start_year} and {end_year} and jurnal LIKE "%{search_pattern}%") LIMIT 10')
	#cur.execute(f'SELECT c_article_id , jurnal, author, affiliate, year FROM tabel_data WHERE year BETWEEN {start_year} and {end_year} and author like "%{search_pattern}%" UNION SELECT tabel_data.c_article_id, tabel_data.jurnal, tabel_data.author, tabel_data.affiliate, tabel_data.year FROM tabel_data, a WHERE tabel_data.year BETWEEN {start_year} and {end_year} and tabel_data.c_article_id = a.c_article_id ORDER BY c_article_id LIMIT 10')
	tampil = cur.fetchall()
	print(tampil)
	if not rows:
			error = "Data tidak ditemukan"
			return render_template("journal.html", error=error)
	else:

	#if not rows:
	#		error = "Data tidak ditemukan"
	#		return render_template("journal.html", rows=rows, error=error)
	#else:
		df = pd.DataFrame()
	if rows:
		cid = [row[0] for row in rows]
		year = [row[1] for row in rows]
		author = [row[2] for row in rows]
		jurnal = [row[3] for row in rows]
		affiliate = [row[4] for row in rows]

		df['c_article_id'] = cid
		df['year'] = year
		df['author'] = author
		df['jurnal'] = jurnal
		df['affiliate'] = affiliate
		print(df)
		df.fillna(0)

		df_cj = pd.DataFrame()
		df_cj['tahun'] = range(awal, akhir)
		df_cj['jumlah paper'] = [len(set(df[(df.year == str(n))].c_article_id)) for n in range(awal,akhir)]
		for x in range(1, 7):
	  		df_cj[str(x) + ' author'] = ngitung_author(x, df)

		df_with_percent = pd.DataFrame()
		df_with_percent['Tahun'] = df_cj['tahun']
		df_with_percent['Jml_Paper'] = df_cj['jumlah paper']
		for x in range(1, 7):
			if x != 6:
				df_with_percent[str(x) + ' Author'] = df_cj[str(x) + ' author']
				df_with_percent['% ' + str(x) + ' Author'] = [str(float(df_cj.iloc[n][str(x) + ' author'])/df_cj.iloc[n]['jumlah paper']*100)[:5] for n in range(len(df_cj[str(x) + ' author']))]
			else:
				df_with_percent[str(x) + ' Author atau lebih'] = df_cj[str(x) + ' author']
				df_with_percent['% ' + str(x) + ' Author atau lebih'] = [str(float(df_cj.iloc[n][str(x) + ' author'])/df_cj.iloc[n]['jumlah paper']*100)[:5] for n in range(len(df_cj[str(x) + ' author']))]
		df_with_percent = df_with_percent[df_with_percent['Tahun'].between(int(start_year), int(end_year), inclusive=True)]
		print(df_with_percent)


		author_jumlah = []
		for x in tqdm(set(list(df.jurnal))):
			author_jumlah.append([x, len(df[(df.jurnal == x)])])
		yak = sorted(author_jumlah, key=operator.itemgetter(1), reverse=True)
		df_muncul_author=pd.DataFrame()
		df_muncul_author['Jurnal']=[n[0] for n in yak]
		df_muncul_author['Jml_Publikasi']=[n[1] for n in yak]
		df_muncul_author.head(10)

	return render_template("journal.html",
		rows=rows,
		tampil=tampil,
		highlight=highlight,
		search_pattern=search_pattern, 
		cols1=df_with_percent.columns, 
		rows1=df_with_percent.iterrows(), 
		cols2=df_muncul_author.columns,
		rows2=df_muncul_author.head(10).iterrows())

@app.route('/author', methods=["GET", "POST"])
def author():
	cur = mysql.connection.cursor()
	search_pattern = ""
	start_year = awal
	end_year = akhir

	if request.method == "POST":
		search_pattern = request.form['search_pattern'] or ""
		start_year = request.form['start_year'] or 1990
		end_year = request.form['end_year'] or 2015

	#cur.execute(f'SELECT c_article_id, year, author, jurnal, affiliate FROM tabel_data WHERE year between {start_year} and {end_year} or author LIKE "%{search_pattern}%"')
	cur.execute(f'SELECT c_article_id, year, author, jurnal, affiliate from tabel_data WHERE c_article_id in (SELECT c_article_id from tabel_data WHERE year BETWEEN {start_year} and {end_year} and author LIKE "%{search_pattern}%")')
	rows = cur.fetchall()
	cur.execute(f'SELECT c_article_id, year, author, jurnal, affiliate from tabel_data WHERE c_article_id in (SELECT c_article_id from tabel_data WHERE year BETWEEN {start_year} and {end_year} and author LIKE "%{search_pattern}%") LIMIT 10')
	#cur.execute(f'SELECT c_article_id, year, author, jurnal, affiliate FROM tabel_data WHERE year between {start_year} and {end_year} or author LIKE "%{search_pattern}%" LIMIT 10')
	tampil = cur.fetchall()
	print(tampil)
	if not rows:
			error = "Data tidak ditemukan"
			return render_template("author.html", error=error)
	else:
		df = pd.DataFrame()
		if rows:
			cid = [row[0] for row in rows]
			year = [row[1] for row in rows]
			author = [row[2] for row in rows]
			jurnal = [row[3] for row in rows]
			affiliate = [row[4] for row in rows]

			df['c_article_id'] = cid
			df['year'] = year
			df['author'] = author
			df['affiliate'] = affiliate
			print(df)
			df.fillna(0)

			df_cj = pd.DataFrame()
			df_cj['tahun'] = range(awal, akhir)
			df_cj['jumlah paper'] = [len(set(df[(df.year == str(n))].c_article_id)) for n in range(awal,akhir)]
			for x in range(1, 7):
	  			df_cj[str(x) + ' author'] = ngitung_author(x, df)

			df_with_percent = pd.DataFrame()
			df_with_percent['Tahun'] = df_cj['tahun']
			df_with_percent['Jml_Paper'] = df_cj['jumlah paper']
			for x in range(1, 7):
				if x != 6:
					df_with_percent[str(x) + ' Author'] = df_cj[str(x) + ' author']
					df_with_percent['% ' + str(x) + ' Author'] = [str(float(df_cj.iloc[n][str(x) + ' author'])/df_cj.iloc[n]['jumlah paper']*100)[:5] for n in range(len(df_cj[str(x) + ' author']))]
				else:
					df_with_percent[str(x) + ' Author atau lebih'] = df_cj[str(x) + ' author']
					df_with_percent['% ' + str(x) + ' Author atau lebih'] = [str(float(df_cj.iloc[n][str(x) + ' author'])/df_cj.iloc[n]['jumlah paper']*100)[:5] for n in range(len(df_cj[str(x) + ' author']))]
			df_with_percent = df_with_percent[df_with_percent['Tahun'].between(int(start_year), int(end_year), inclusive=True)]
			print(df_with_percent)


			author_jumlah = []
			for x in tqdm(set(list(df.author))):
				author_jumlah.append([x, len(df[(df.author == x)])])
			yak = sorted(author_jumlah, key=operator.itemgetter(1), reverse=True)
			df_muncul_author=pd.DataFrame()
			df_muncul_author['Author']=[n[0] for n in yak]
			df_muncul_author['Jml_Publikasi']=[n[1] for n in yak]
			df_muncul_author.head(10)

		return render_template("author.html",
			rows=rows,
			tampil=tampil,
			highlight=highlight,
			search_pattern=search_pattern, 
			cols1=df_with_percent.columns, 
			rows1=df_with_percent.iterrows(), 
			cols2=df_muncul_author.columns,
			rows2=df_muncul_author.head(10).iterrows())
	return render_template("author.html")

@app.route("/search_affiliation", methods=["GET", "POST"])
def search_affiliation():
	if request.method == "POST":
		cur = mysql.connection.cursor()
		start_year = request.form['start_year'] or awal
		end_year = request.form['end_year'] or akhir
		affiliation_name = request.form['affiliation_name']

		#cur.execute(f'SELECT c_article_id, year, author, jurnal, affiliate FROM tabel_data WHERE year between {start_year} and {end_year} and affiliate LIKE "%{affiliation_name}%"')
		#rows_aff = cur.fetchall()
		cur.execute(f'SELECT affiliate, year, count(affiliate) FROM tabel_data WHERE year between {start_year} and {end_year} and affiliate LIKE "%{affiliation_name}%" group by year order by year desc')
		rows_aff = cur.fetchall()

	
		if not rows_aff:
			error = "Data tidak ditemukan"
			return render_template("affiliation.html", rows_aff=rows_aff, error=error)
		else:
			return render_template("affiliation.html", rows_aff=rows_aff, highlight=highlight, affiliation_name=affiliation_name)
	return render_template("affiliation.html")

if __name__ == '__main__':
    app.run(debug=True)