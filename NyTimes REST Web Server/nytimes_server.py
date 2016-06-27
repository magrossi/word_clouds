from flask import Flask, request, jsonify
import mysql.connector

app = Flask(__name__, static_url_path='')

@app.route('/', methods=['GET'])
def root():
	return app.send_static_file('index.html')

# Dates - returns { max_date: <value>, min_date: <value> }
# in: <>
# out: { min_date: <value>, max_date: <value> }
@app.route('/api/v1.0/dates', methods=['GET'])
def get_dates():
	connection = mysql.connector.connect(user='nytimes_ro', database='db_nytimes')
	cursor = connection.cursor() #(buffered=True)
	query = ("SELECT MIN(doc_date) as max_date, MAX(doc_date) as min_date FROM document")
	cursor.execute(query)
	result = {}
	for (min_date, max_date) in cursor:
		result['min_date'] = min_date.isoformat()
		result['max_date'] = max_date.isoformat()
	cursor.close()
	connection.close()
	return jsonify(result=result)

# Document count per date interval
# in: start date, end date
# out: [{ date: <value>, count: <value> }, {}, ..]
@app.route('/api/v1.0/CountPerDate', methods=['GET'])
def get_countperdate():
	startDate = request.args.get('startdate')
	endDate = request.args.get('enddate')
	connection = mysql.connector.connect(user='nytimes_ro', database='db_nytimes')
	cursor = connection.cursor()
	cursor.callproc('spGetDailyDocumentCount', args=(startDate, endDate))
	results = []
	for stored_results in cursor.stored_results():
		rows = stored_results.fetchall()
		for row in rows:
			result = {}
			result['date'] = row[0].isoformat()
			result['count'] = long(row[1])
			results.append(result)
	return jsonify (result=results)

# Category count per date interval
# in: start date, end date
# out: [{ category: <value>, count: <value>}, ..]
@app.route('/api/v1.0/CountPerCategory', methods=['GET'])
def get_countpercategory():
	startDate = request.args.get('startdate')
	endDate = request.args.get('enddate')
	connection = mysql.connector.connect(user='nytimes_ro', database='db_nytimes')
	cursor = connection.cursor()
	cursor.callproc('spGetCategoryCount', args=(startDate, endDate))
	results = []
	for stored_results in cursor.stored_results():
		rows = stored_results.fetchall()
		for row in rows:
			result = {}
			result['id'] = row[0]
			result['category'] = row[1]
			result['count'] = long(row[2])
			results.append(result)
	return jsonify (result=results)

# Term daily count per category
# in: term, start date, end date
# out: [{ name: <value>, counts: [{date: <value>, count: <value>}, ..], ..]
@app.route('/api/v1.0/CategoryCountPerTerm', methods=['GET'])
def get_categorycountperterm():
	term = request.args.get('term')
	startDate = request.args.get('startdate')
	endDate = request.args.get('enddate')
	connection = mysql.connector.connect(user='nytimes_ro', database='db_nytimes')
	cursor = connection.cursor()
	cursor.callproc('spGetTermDailyCountPerCategory', args=(term, startDate, endDate))
	results = []
	category = {}
	for stored_results in cursor.stored_results():
		rows = stored_results.fetchall()
		for row in rows:
			if not category:
				category['name'] = row[0]
				category['counts'] = []
			else:
				if category['name'] != row[0]:
					results.append(category)
					category = {}
					category['name'] = row[0]
					category['counts'] = []
			result = {}
			result['date'] = row[1].isoformat()
			result['count'] = long(row[2])
			category['counts'].append(result)
	if category:
		results.append(category)
	return jsonify (result=results)

# Top 500 terms for date interval (all categories)
# in: start date, end date, categories (optional)
# out: [{ term: <value>, tf: <value>, num_docs: <value>, tot_docs: <value>, tf_idf: <value> }, ..]
@app.route('/api/v1.0/TopWords', methods=['GET'])
def get_topwords():
	startDate = request.args.get('startdate')
	endDate = request.args.get('enddate')
	categories = request.args.get('categories')
	connection = mysql.connector.connect(user='nytimes_ro', database='db_nytimes')
	cursor = connection.cursor()
	if categories:
		cursor.callproc('spGetWordCloudCat', args=(startDate, endDate, categories, 250))
	else:
		cursor.callproc('spGetWordCloud', args=(startDate, endDate, 250))
	results = {}
	results['tot_docs'] = 0
	results['terms'] = []
	for stored_results in cursor.stored_results():
		rows = stored_results.fetchall()
		for row in rows:
			result = {}
			result['term'] = row[0]
			result['tf'] = int(row[1])
			result['num_docs'] = int(row[2])
			result['tf_idf'] = float(row[4])
			results['tot_docs'] = int(row[3]) if (int(row[3]) > results['tot_docs']) else results['tot_docs']
			results['terms'].append(result)
	return jsonify (result=results)

if __name__ == '__main__':
    app.run(debug=True)