from flask import Flask, render_template, request
from flask_mysqldb import MySQL
from flask_table import Table, Col
import pandas as pd
from tqdm import tqdm
import operator
import re
import math

from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.resources import INLINE
from bokeh.util.string import encode_utf8

from bokeh.core.properties import value
from bokeh.models import ColumnDataSource
from bokeh.transform import dodge

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
	start_year = 1990
	end_year = 1991

	if request.method == "POST":
		search_pattern = request.form['search_pattern'] or ""
		start_year = request.form['start_year'] or 1990
		end_year = request.form['end_year'] or 2015

	cur.execute(f'SELECT c_article_id, jurnal, author, affiliate, year from tabel_data WHERE c_article_id in (SELECT c_article_id from tabel_data WHERE year BETWEEN {start_year} and {end_year} and jurnal LIKE "%{search_pattern}%") group by c_article_id')
	ambil =  cur.fetchall()
	cur.execute(f'SELECT c_article_id, jurnal, author, affiliate, year from tabel_data WHERE c_article_id in (SELECT c_article_id from tabel_data WHERE year BETWEEN {start_year} and {end_year} and jurnal LIKE "%{search_pattern}%")')
	rows = cur.fetchall()
	cur.execute(f'SELECT c_article_id, jurnal, author, affiliate, year from tabel_data WHERE c_article_id in (SELECT c_article_id from tabel_data WHERE year BETWEEN {start_year} and {end_year} and jurnal LIKE "%{search_pattern}%") LIMIT 20')
	tampil = cur.fetchall()

	if not rows:
			error = "Data tidak ditemukan"
			return render_template("journal.html", error=error)
	else:
		df = pd.DataFrame()

	if ambil:
		df_ambil =  pd.DataFrame()
		art_id = [row[0] for row in ambil]
		jurnal_ambil = [row[1] for row in ambil]

		df_ambil['c_article_id'] = art_id
		df_ambil['jurnal'] = jurnal_ambil
		


	if rows:
		cid = [row[0] for row in rows]
		jurnal = [row[1] for row in rows]
		author = [row[2] for row in rows]
		affiliate = [row[3] for row in rows]
		year = [row[4] for row in rows]

		df['c_article_id'] = cid
		df['year'] = year
		df['author'] = author
		df['jurnal'] = jurnal
		df['affiliate'] = affiliate
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
				df_with_percent['% ' + str(x) + ' Author'] = [str(float(df_cj.iloc[n][str(x) + ' author'])/df_cj.iloc[n]['jumlah paper']*100)[:5] if df_cj.iloc[n]['jumlah paper'] != 0 else str(0.0) for n in range(len(df_cj[str(x) + ' author']))]
			else:
				df_with_percent[str(x) + ' Author atau lebih'] = df_cj[str(x) + ' author']
				df_with_percent['% ' + str(x) + ' Author atau lebih'] = [str(float(df_cj.iloc[n][str(x) + ' author'])/df_cj.iloc[n]['jumlah paper']*100)[:5] if df_cj.iloc[n]['jumlah paper'] != 0 else str(0.0) for n in range(len(df_cj[str(x) + ' author']))]
		df_with_percent = df_with_percent[df_with_percent['Tahun'].between(int(start_year), int(end_year), inclusive=True)]

		author_jumlah = []
		for x in tqdm(set(list(df_ambil.jurnal))):
			author_jumlah.append([x, len(df_ambil[(df_ambil.jurnal == x)])])
		yak = sorted(author_jumlah, key=operator.itemgetter(1), reverse=True)
		df_muncul_author=pd.DataFrame()
		df_muncul_author['Jurnal']=[n[0] for n in yak]
		df_muncul_author['Jml_Publikasi']=[n[1] for n in yak]
		df_muncul_author.head(10)

		data_tahun = df_with_percent['Tahun']
		data_author = df_with_percent[['1 Author', '2 Author', '3 Author', '4 Author', '5 Author', '6 Author atau lebih']]

		years = [str(year) for year in data_tahun]
		authors = {col:[int(df_with_percent[df_with_percent['Tahun'] == int(year)][col]) for year in years] for col in data_author.columns}
		authorship = {'years': years, **authors}
		colors = ["#2ecc71", "#3498db", "#9b59b6", "#f1c40f", "#e74c3c", "#34495e"]
		source = ColumnDataSource(data=authorship)
		TOOLS="hover, wheel_zoom, box_zoom"

		TOOLTIPS = [
		    ("Tahun", "@years"),
		    ("1 Author", "@{1 Author}"),
		    ("2 Author", "@{2 Author}"),
		    ("3 Author", "@{3 Author}"),
		    ("4 Author", "@{4 Author}"),
		    ("5 Author", "@{5 Author}"),
		    ("6 Author atau lebih", "@{6 Author atau lebih}"),
		]

		max_y = data_author.values.max() + 50
		js_resources = INLINE.render_js()
		css_resources = INLINE.render_css()
		
		p = figure(x_range=years, y_range=(0, max_y), plot_height=300, tooltips=TOOLTIPS, title="Grafik Co-Authorship")
		pos = -0.3
		i = 0
		for col in data_author.columns:
			p.vbar(x=dodge('years', pos, range=p.x_range), top=col, width=0.1, source=source, color=colors[i % 6], legend=value(col))
			pos += 0.1
			i += 1

		p.x_range.range_padding = 0.1
		p.xgrid.grid_line_color = None
		p.legend.location = "top_left"
		p.legend.orientation = "horizontal"
		p.sizing_mode = 'scale_width'

		script, div = components(p)

	return render_template("journal.html",
		rows=rows,
		tampil=tampil,
		highlight=highlight,
		search_pattern=search_pattern, 
		cols1=df_with_percent.columns, 
		rows1=df_with_percent.iterrows(),
		sum1=df_with_percent['Jml_Paper'].sum(),
		cols2=df_muncul_author.columns,
		rows2=df_muncul_author.head(10).iterrows(),
		plot_script=script,
	    plot_div=div,
	    js_resources=js_resources,
	    css_resources=css_resources)

@app.route('/author', methods=["GET", "POST"])
def author():
	cur = mysql.connection.cursor()
	search_pattern = ""
	start_year = 1990	
	end_year = 1991

	if request.method == "POST":
		search_pattern = request.form['search_pattern'] or ""
		start_year = request.form['start_year'] or 1990
		end_year = request.form['end_year'] or 2015

	cur.execute(f'SELECT c_article_id, year, author, jurnal, affiliate from tabel_data WHERE c_article_id in (SELECT c_article_id from tabel_data WHERE year BETWEEN {start_year} and {end_year} and author LIKE "%{search_pattern}%")')
	rows = cur.fetchall()
	cur.execute(f'SELECT c_article_id, year, author, jurnal, affiliate from tabel_data WHERE c_article_id in (SELECT c_article_id from tabel_data WHERE year BETWEEN {start_year} and {end_year} and author LIKE "%{search_pattern}%") LIMIT 20')
	tampil = cur.fetchall()
	
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
					df_with_percent['% ' + str(x) + ' Author'] = [str(float(df_cj.iloc[n][str(x) + ' author'])/df_cj.iloc[n]['jumlah paper']*100)[:5] if df_cj.iloc[n]['jumlah paper'] != 0 else str(0.0) for n in range(len(df_cj[str(x) + ' author']))]
				else:
					df_with_percent[str(x) + ' Author atau lebih'] = df_cj[str(x) + ' author']
					df_with_percent['% ' + str(x) + ' Author atau lebih'] = [str(float(df_cj.iloc[n][str(x) + ' author'])/df_cj.iloc[n]['jumlah paper']*100)[:5] if df_cj.iloc[n]['jumlah paper'] != 0 else str(0.0) for n in range(len(df_cj[str(x) + ' author']))]
			df_with_percent = df_with_percent[df_with_percent['Tahun'].between(int(start_year), int(end_year), inclusive=True)]

			author_jumlah = []
			for x in tqdm(set(list(df.author))):
				author_jumlah.append([x, len(df[(df.author == x)])])
			yak = sorted(author_jumlah, key=operator.itemgetter(1), reverse=True)
			df_muncul_author=pd.DataFrame()
			df_muncul_author['Author']=[n[0] for n in yak]
			df_muncul_author['Jml_Publikasi']=[n[1] for n in yak]
			df_muncul_author.head(10)

			data_tahun = df_with_percent['Tahun']
			data_author = df_with_percent[['1 Author', '2 Author', '3 Author', '4 Author', '5 Author', '6 Author atau lebih']]

			years = [str(year) for year in data_tahun]
			authors = {col:[int(df_with_percent[df_with_percent['Tahun'] == int(year)][col]) for year in years] for col in data_author.columns}
			authorship = {'years': years, **authors}
			colors = ["#2ecc71", "#3498db", "#9b59b6", "#f1c40f", "#e74c3c", "#34495e"]

			source = ColumnDataSource(data=authorship)
			TOOLS="hover, wheel_zoom, box_zoom"

			TOOLTIPS = [
			    ("Tahun", "@years"),
			    ("1 Author", "@{1 Author}"),
			    ("2 Author", "@{2 Author}"),
			    ("3 Author", "@{3 Author}"),
			    ("4 Author", "@{4 Author}"),
			    ("5 Author", "@{5 Author}"),
			    ("6 Author atau lebih", "@{6 Author atau lebih}"),
			]

			max_y = data_author.values.max() + 50
			js_resources = INLINE.render_js()
			css_resources = INLINE.render_css()
			
			p = figure(x_range=years, y_range=(0, max_y), plot_height=300, tooltips=TOOLTIPS, title="Grafik Co-Authorship")
			pos = -0.3
			i = 0
			for col in data_author.columns:
				p.vbar(x=dodge('years', pos, range=p.x_range), top=col, width=0.1, source=source, color=colors[i % 6], legend=value(col))
				pos += 0.1
				i += 1

			p.x_range.range_padding = 0.1
			p.xgrid.grid_line_color = None
			p.legend.location = "top_left"
			p.legend.orientation = "horizontal"
			p.sizing_mode = 'scale_width'

			script, div = components(p)

		return render_template("author.html",
			rows=rows,
			tampil=tampil,
			highlight=highlight,
			search_pattern=search_pattern, 
			cols1=df_with_percent.columns, 
			rows1=df_with_percent.iterrows(),
			sum1=df_with_percent['Jml_Paper'].sum(), 
			cols2=df_muncul_author.columns,
			rows2=df_muncul_author.head(10).iterrows(),
			plot_script=script,
	        plot_div=div,
	        js_resources=js_resources,
	        css_resources=css_resources)
	return render_template("author.html")

@app.route("/search_affiliation", methods=["GET", "POST"])
def search_affiliation():
	cur = mysql.connection.cursor()
	affiliation_name = ""
	start_year = 1990
	end_year = 1991

	if request.method == "POST":
		cur = mysql.connection.cursor()
		start_year = request.form['start_year'] or 1990
		end_year = request.form['end_year'] or 2015
		affiliation_name = request.form['affiliation_name'] or ""

	cur.execute(f'SELECT c_article_id, affiliate, author, jurnal, year from tabel_data WHERE c_article_id in (SELECT c_article_id from tabel_data WHERE year BETWEEN {start_year} and {end_year} and affiliate LIKE "%{affiliation_name}%") LIMIT 20')
	rows_aff = cur.fetchall()
	cur.execute(f'SELECT c_article_id, affiliate, author, jurnal, year from tabel_data WHERE c_article_id in (SELECT c_article_id from tabel_data WHERE year BETWEEN {start_year} and {end_year} and affiliate LIKE "%{affiliation_name}%")')
	rows = cur.fetchall()
	
	if not rows_aff:
		error = "Data tidak ditemukan"
		return render_template("affiliation.html", error=error)
	else:
		df = pd.DataFrame()

		if rows:
			cid = [row[0] for row in rows]
			affiliate = [row[1] for row in rows]
			author = [row[2] for row in rows]
			jurnal = [row[3] for row in rows]
			year = [row[4] for row in rows]

			df['c_article_id'] = cid
			df['year'] = year
			df['author'] = author
			df['affiliate'] = affiliate
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
					df_with_percent['% ' + str(x) + ' Author'] = [str(float(df_cj.iloc[n][str(x) + ' author'])/df_cj.iloc[n]['jumlah paper']*100)[:5] if df_cj.iloc[n]['jumlah paper'] != 0 else str(0.0) for n in range(len(df_cj[str(x) + ' author']))]
				else:
					df_with_percent[str(x) + ' Author atau lebih'] = df_cj[str(x) + ' author']
					df_with_percent['% ' + str(x) + ' Author atau lebih'] = [str(float(df_cj.iloc[n][str(x) + ' author'])/df_cj.iloc[n]['jumlah paper']*100)[:5] if df_cj.iloc[n]['jumlah paper'] != 0 else str(0.0)  for n in range(len(df_cj[str(x) + ' author']))]
			df_with_percent = df_with_percent[df_with_percent['Tahun'].between(int(start_year), int(end_year), inclusive=True)]
	
			author_jumlah = []
			for x in tqdm(set(list(df.affiliate))):
				author_jumlah.append([x, len(df[(df.affiliate == x)])])
			yak = sorted(author_jumlah, key=operator.itemgetter(1), reverse=True)
			df_muncul_author=pd.DataFrame()
			df_muncul_author['Afiliasi']=[n[0] for n in yak]
			df_muncul_author['Jumlah']=[n[1] for n in yak]
			df_muncul_author.head(10)

			data_tahun = df_with_percent['Tahun']
			data_author = df_with_percent[['1 Author', '2 Author', '3 Author', '4 Author', '5 Author', '6 Author atau lebih']]

			years = [str(year) for year in data_tahun]
			authors = {col:[int(df_with_percent[df_with_percent['Tahun'] == int(year)][col]) for year in years] for col in data_author.columns}
			authorship = {'years': years, **authors}
			colors = ["#2ecc71", "#3498db", "#9b59b6", "#f1c40f", "#e74c3c", "#34495e"]

			source = ColumnDataSource(data=authorship)
			TOOLS="hover, wheel_zoom, box_zoom"

			TOOLTIPS = [
			    ("Tahun", "@years"),
			    ("1 Author", "@{1 Author}"),
			    ("2 Author", "@{2 Author}"),
			    ("3 Author", "@{3 Author}"),
			    ("4 Author", "@{4 Author}"),
			    ("5 Author", "@{5 Author}"),
			    ("6 Author atau lebih", "@{6 Author atau lebih}"),
			]

			max_y = data_author.values.max() + 50
			js_resources = INLINE.render_js()
			css_resources = INLINE.render_css()
		
			p = figure(x_range=years, y_range=(0, max_y), plot_height=300, tooltips=TOOLTIPS, title="Grafik Co-Authorship")
			pos = -0.3
			i = 0
			for col in data_author.columns:
				p.vbar(x=dodge('years', pos, range=p.x_range), top=col, width=0.1, source=source, color=colors[i % 6], legend=value(col))
				pos += 0.1
				i += 1

			p.x_range.range_padding = 0.1
			p.xgrid.grid_line_color = None
			p.legend.location = "top_left"
			p.legend.orientation = "horizontal"
			p.sizing_mode = 'scale_width'

			script, div = components(p)

		return render_template("affiliation.html", 
			rows=rows,
			rows_aff=rows_aff,
			highlight=highlight,
			affiliation_name=affiliation_name, 
			cols1=df_with_percent.columns, 
			rows1=df_with_percent.iterrows(), 
			sum1=df_with_percent['Jml_Paper'].sum(),
			cols2=df_muncul_author.columns,
			rows2=df_muncul_author.head(10).iterrows(),
			plot_script=script,
	        plot_div=div,
	        js_resources=js_resources,
	        css_resources=css_resources)
	return render_template("affiliation.html")

if __name__ == '__main__':
    app.run(debug=True)