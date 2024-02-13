import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from whoosh.fields import Schema, TEXT, ID
from whoosh.index import create_in, open_dir
from whoosh.qparser import QueryParser
from whoosh import scoring
from whoosh.index import LockError
import time
import schedule
import sys  # Import sys module for sys.exit()

# Function to crawl and index data from the Coventry University Research Centre for Health and Life Sciences (RCHL) portal
def fetch_and_index_data(source_url, index_folder):
    # Fetch the page containing the list of publications
    response = requests.get(source_url)
    parsed_html = BeautifulSoup(response.text, 'html.parser')

    # Define the schema for Whoosh index
    index_schema = Schema(title=TEXT(stored=True), authors=TEXT(stored=True), year=ID(stored=True), 
                    publication_url=ID(stored=True, unique=True), author_profile_url=ID(stored=True))
    
    # Create the index folder if it doesn't exist
    if not os.path.exists(index_folder):
        os.mkdir(index_folder)
        
    index_object = create_in(index_folder, index_schema)
    writer = index_object.writer()

    # Extract publication information
    for publication_div in parsed_html.find_all('div', class_='result-container'):
        title_tag = publication_div.find('h3', class_="title")
        title = title_tag.get_text(strip=True) if title_tag else "N/A"

        authors_tags = publication_div.find_all('a', class_='link person')
        authors = [author.text.strip() for author in authors_tags] if authors_tags else ["N/A"]
        authors_str = ', '.join(authors)

        year_tag = publication_div.find('span', class_='date')
        year = year_tag.text.strip() if year_tag else "N/A"

        publication_url_tag = publication_div.find('a', class_='title')
        publication_url = urljoin(source_url, publication_url_tag['href']) if publication_url_tag else "N/A"

        author_profile_url_tag = publication_div.find('a', class_='link person')
        author_profile_url = urljoin(source_url, author_profile_url_tag['href']) if author_profile_url_tag else "N/A"
        
        # Add data to the Whoosh index
        try:
            writer.add_document(title=title, authors=authors_str, year=year,
                                publication_url=publication_url, author_profile_url=author_profile_url)
        except LockError as e:
            print(f"LockError: {e}")
            print("Attempting to clean up lock files...")

            # Manually clean up lock files
            lock_file_path = f"{index_folder}/write.lock"
            try:
                os.remove(lock_file_path)
                print(f"Lock file {lock_file_path} removed.")
            except Exception as cleanup_error:
                print(f"Error cleaning up lock file: {cleanup_error}")

    # Commit changes to the index
    writer.commit()

# Function to update index periodically
def perform_index_update(base_url, index_path):
    print("Updating index...")
    fetch_and_index_data(base_url, index_path)
    print("Index updated.")

# Function to search the index and return results
def execute_search(query_string, index_folder):
    index_object = open_dir(index_folder)
    results = []
    with index_object.searcher(weighting=scoring.TF_IDF()) as searcher:
        query_parser = QueryParser("title", index_object.schema)
        query = query_parser.parse(query_string)
        search_results = searcher.search(query, terms=True)

        # Append search results to a list
        for result in search_results:
            results.append({
                'title': result['title'],
                'authors': result['authors'],
                'year': result['year'],
                'publication_url': result['publication_url'],
                'author_profile_url': result['author_profile_url']
            })
    return results


# Schedule index update task to run once per week
schedule.every().week.do(perform_index_update, base_url="https://pureportal.coventry.ac.uk/en/organisations/ihw-centre-for-health-and-life-sciences-chls/publications/", index_path="storage")

# Call perform_index_update initially to create the index
perform_index_update("https://pureportal.coventry.ac.uk/en/organisations/ihw-centre-for-health-and-life-sciences-chls/publications/", "storage")

# User interface for querying publications
def run_user_interface():
    while True:
        user_query = input("Enter your query (press 'q' to quit): ")
        if user_query.lower() == 'q':
            break  # Exit the loop if 'q' is entered
        execute_search(user_query, "storage")
    sys.exit()  # Exit the script once the user quits


# Run the scheduled tasks and user interface
if __name__ == "__main__":
    while True:
        schedule.run_pending()
        run_user_interface()
        time.sleep(1)
