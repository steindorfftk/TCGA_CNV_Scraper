from bs4 import BeautifulSoup
import requests
from time import sleep
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium.common.exceptions import NoAlertPresentException
from selenium.common.exceptions import NoSuchElementException
from urllib.parse import urlparse, urljoin
import time
from selenium.webdriver.support.ui import Select
import re
from selenium.common.exceptions import StaleElementReferenceException

def read_genes():
	genes = []
	with open('Gene_names.txt', 'r') as texto:
		for line in texto:
			linha = line.split()
			if len(linha) > 0:
				genes.append(linha[0])
	with open('Output.csv','r') as texto:
		done_genes = []
		for line in texto:
			if 'Gene' not in line:
				linha = line.replace(';',' ').split()
				done_genes.append(linha[0].replace('"',''))
	remaining_genes = [value for value in genes if value not in done_genes]
	return remaining_genes

def main():
	start_time = time.time()
	i = 0
	genes = read_genes()
	print(f'Scraping {len(genes)} genes') 
	if 'Output.csv' not in os.listdir():
		with open('Output.csv','w') as data_t:
			data_t.write('Gene;Count;Cancers\n')
	genome_dic = {}
	firefox_options = Options()
	firefox_options.add_argument('--headless')
	driver = webdriver.Firefox(options=firefox_options)
	driver.get('https://portals.broadinstitute.org/tcga/gistic/browseGisticByGene#')
	for gene in genes:
		try:
			print(f'Searching {gene}')	
			gene_dic = {}
			genome_dic[gene] = []
			current_values = []
			start_time = time.time()
			i = 0
			
			# Selecting value in dropdown
			select_element = WebDriverWait(driver, 10).until(
			    EC.element_to_be_clickable((By.ID, 'searchForm:gisticAnalysisDecorator:gisticAnalysis'))
			)
			select = Select(select_element)
			select.select_by_value('0')
			
			# Entering gene in the input field
			input_element = WebDriverWait(driver, 10).until(
			    EC.presence_of_element_located((By.ID, 'searchForm:geneSymbolDecorator:geneSymbol'))
			)
			input_element.send_keys(gene)
			
			# Clicking the search button
			button_element = WebDriverWait(driver, 10).until(
			    EC.element_to_be_clickable((By.ID, 'searchForm:searchButton'))
			)
			button_element.click()
			try:
				element = WebDriverWait(driver, 4).until(EC.presence_of_element_located((By.ID, 'searchResultsForm:dels_lbl')))
				td_element = driver.find_element('id','searchResultsForm:dels_lbl')
				td_element.click()
				page_source = driver.page_source
				lines = page_source.split('\n')
				for line in lines:
					if 'id209' in line:
						data_line = line
				linha=data_line.replace(' ','_').replace('=',' ').split()
				for value in linha:
					if 'this_cancer_type' in value or 'id209' in value or 'id220' in value:
						if 'broadinstitute' not in value and 'opacity' not in value:
							current_values.append(value)
							if len(current_values) == 3:
				       				match1 = re.search(r'>(.*?)</a>', current_values[0])
				       				key = match1.group(1).replace('_',' ')
				       				match2 = re.search(r'>(.*?)</td>', current_values[1])
				       				yesno = match2.group(1)
				       				match3 = re.search(r'>(.*?)</td>', current_values[2])
				       				sign = eval(match3.group(1))
				       				gene_dic[key] = [yesno,sign]
				       				current_values = []
				if len(gene_dic.keys()) > 0:			
					for key, value in gene_dic.items():
						if gene_dic[key][0] == 'Yes' and gene_dic[key][1] < 0.25:
							genome_dic[gene].append(key)
					with open('Output.csv','a') as data_t:
						count = 0
						for value in genome_dic[gene]:
							count+=1
						data_t.write(f'{gene};{count};{genome_dic[gene]}\n')
						data_t.flush()	
				end_time = time.time()
				i += 1
				elapsed_time = end_time - start_time
				mean_time = round(elapsed_time/i, 2)
				print(f'{gene} done! {mean_time}/gene')
				driver.refresh()
			except TimeoutException:
				with open('Output.csv','a') as data_t:
					data_t.write(f'{gene};NA;Not found\n')
				driver.refresh()		
				end_time = time.time()
				i += 1
				elapsed_time = end_time - start_time
				mean_time = round(elapsed_time/i, 2)
				print(f'{gene} done! {mean_time}/gene')		
		except StaleElementReferenceException:
    			print(f"StaleElementReferenceException occurred for gene: {gene}")
    			driver.refresh()
    			continue  # Skip to the next iteration
		


main()



