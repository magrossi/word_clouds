class Term():
   term_id = 0
   term = ''

   def ToCSV(self):
      return '"{0}";"{1}"\n'.format(self.term_id, self.term)

class Cat():
   cat_id = 0
   cat_name = ''

   def ToCSV(self):
      return '"{0}";"{1}"\n'.format(self.cat_id, self.cat_name)

class Doc():
   doc_id = 0
   doc_date = '0001-01-01'
   cat_id = 0
   url = ''

   def ToCSV(self):
      return '"{0}";"{1}";"{2}";"{3}"\n'.format(self.doc_id, self.doc_date, self.cat_id, self.url)

class TermTF():
   term_id = 0
   doc_id = 0
   tf = 0
   tf_norm = 0.000000000

   def ToCSV(self):
      return '"{0}";"{1}";"{2}";"{3}"\n'.format(self.term_id, self.doc_id, self.tf, self.tf_norm)