import requests
import time
from bs4 import BeautifulSoup
from requests import RequestException

website = 'datalaboratory.one'
head = 'https://'
first_link = head + website + '/'
dumping_factor = 0.85
iterations = 50


class Page:

    def __init__(self, link: str, incoming_link: str):
        self.outgoing_links = set()
        self.incoming_links = set()
        self.link = link
        self.incoming_links.add(incoming_link)
        self.page_rank = 1

    def process_page(self):
        try:
            time.sleep(1)
            text = requests.get(self.link, timeout=10).text
        except RequestException:
            return None
        soup = BeautifulSoup(markup=text, features="lxml")
        alla = soup.find_all('a', href=True)
        for a in alla:
            if str(a['href']).__contains__('http') and str(a['href']).__contains__('://' + website):
                self.outgoing_links.add(a['href'])


def create_dot_file(dictionary: dict, filename: str):
    f = open(filename + ".dot", "w")
    f.write("digraph " + filename + " {\n")
    for link in dictionary:
        page: Page = dictionary[link]
        for outgoing_link in page.outgoing_links:
            if outgoing_link is not None:
                f.write('\"' + link + '\"->\"' + outgoing_link + '\";\n')
    f.write('}')
    f.close()


def process(link: str, pages: dict, depth_level: int, depth_limit: int):
    for page in pages[link].outgoing_links:
        if pages.keys().__contains__(page):
            if not pages[page].incoming_links.__contains__(link):
                pages[page].incoming_links.add(link)
            return pages
        else:
            if depth_level < depth_limit:
                pages[page] = process_page(link=page, incoming_link=link)
                process(link=page, pages=pages, depth_level=depth_level + 1, depth_limit=depth_limit)
            else:
                pages[page] = Page(link=page, incoming_link=link)
    return pages


def process_page(link: str, incoming_link: str):
    page = Page(link=link, incoming_link=incoming_link)
    page.process_page()
    return page


def calculate_page_rank(d_factor: float, matrix: list, iters):
    length = len(matrix)
    vector2 = [((1 - d_factor) / length) for _ in range(length)]
    pr_vector = [1 / length for _ in range(length)]

    for i in range(length):
        for j in range(length):
            matrix[i][j] *= d_factor

    for i in range(iters):
        vector1 = matrix_vector_multiply(matrix, pr_vector)
        pr_vector = vectors_addition(vector1, vector2)
    return pr_vector


def matrix_vector_multiply(matrix: list, vector: list):
    length = len(matrix)
    result_vector = [0 for _ in range(length)]
    for i in range(length):
        for j in range(length):
            result_vector[i] += matrix[i][j] * vector[j]
    return result_vector


def value_vector_multiply(value, vector: list):
    for v in vector:
        v *= value
    return vector


def vectors_addition(vector1: list, vector2: list):
    for i in range(len(vector1)):
        vector1[i] += vector2[i]
    return vector1


def get_transition_matrix(dictionary: dict):
    length = len(dictionary)
    keys = list(dictionary.keys())
    matrix = [[0] * length for _ in range(length)]
    for i in range(length):
        page: Page = dictionary.get(keys[i])
        for j in range(length):
            if keys[j] in page.outgoing_links:
                matrix[j][i] = 1 / len(dictionary.get(keys[j]).outgoing_links)
    return matrix


def print_result(dictionary: dict, vector: list):
    keys = list(dictionary.keys())

    sum_of_page_ranks = 0
    for i in range(len(keys)):
        sum_of_page_ranks += vector[i]
        print(keys[i], "-", vector[i])
    print('\n\n' + str(sum_of_page_ranks))


def clear_dead_ends(dictionary: dict, depth_level: int, depth_limit: int):
    keys = list(dictionary.keys())
    for key in keys:
        page: Page = dictionary[key]
        if len(page.outgoing_links) == 0 or (len(page.outgoing_links) == 1 and page.outgoing_links.__contains__(None)):
            for link in page.incoming_links:
                if link is not None:
                    incoming_page: Page = dictionary[link]
                    incoming_page.outgoing_links.discard(key)
            dictionary.pop(key)
        else:
            links = set(page.outgoing_links)
            for link in links:
                if link is not None:
                    if not keys.__contains__(link):
                        page.outgoing_links.discard(link)
    if depth_level < depth_limit:
        dictionary = clear_dead_ends(dictionary, depth_level + 1, depth_limit)
    return dictionary


if __name__ == '__main__':
    all_pages = {first_link: process_page(link=first_link, incoming_link=None)}
    all_pages = process(link=first_link, depth_level=1, depth_limit=3, pages=all_pages)

    create_dot_file(dictionary=all_pages, filename="result_graph")
    transition_matrix = get_transition_matrix(all_pages)
    page_rank_vector = calculate_page_rank(dumping_factor, transition_matrix, iterations)
    print_result(all_pages, page_rank_vector)

    cleared_pages = dict(all_pages)
    cleared_pages = clear_dead_ends(cleared_pages, 0, 20)

    create_dot_file(dictionary=cleared_pages, filename="cleared_result_graph")
    cleared_transition_matrix = get_transition_matrix(cleared_pages)
    cleared_page_rank_vector = calculate_page_rank(dumping_factor, cleared_transition_matrix, iterations)
    print_result(cleared_pages, cleared_page_rank_vector)
    for line in cleared_transition_matrix:
        for element in range(len(line)):
            line[element] = round(line[element], 3)
        output = line.__str__()
        output = output.replace("0.0,", "0.000,")
        output = output.replace("0.0]", "0.000]")
        print(output)
