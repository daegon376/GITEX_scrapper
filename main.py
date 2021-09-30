import requests
import pandas as pd

from bs4 import BeautifulSoup

SPEAKERS_URL = 'https://gitex.com/speakers/'

EDU_KEYWORDS = ['education', 'educational', 'ministry of education', 'higher education', 'learning', 'ph.d.',
                'digital learning', 'edtech', 'edutech', 'exam', 'teacher', 'professor']
OTHER_KEYWORDS = ['chief executive officer', 'ceo', 'cmo', 'coo', 'founder', 'proctoring', 'artificial intelligence',
                  ' ai ', 'machine learning', ' ml', 'start-up', 'ministries', 'government', 'govt']

DROPOUT_KEYWORDS = ['filmmaker', 'actor', 'singer', 'artist', 'trader', 'blogger', 'vlogger', 'creative', 'model',
                    'ambassador', 'author', 'fashion']

SCORE_PASSING_VAL = 2


def load_page(link):
    page = requests.get(link)
    assert page.status_code == 200
    soup = BeautifulSoup(page.content, 'html.parser')
    return soup


def speakers_to_dict(speakers):
    scores = []
    names = []
    countries = []
    keywords = []
    occupation = []
    bio = []
    links = []
    social = []

    for person in speakers:
        scores.append(int(person.score))
        names.append(person.name)
        countries.append(person.country)
        keywords.append(', '.join(person.keywords))
        occupation.append(person.occupation)
        bio.append(person.bio)
        links.append(person.link)
        social.append(', '.join(person.social_networks))

    speakers_dict = {'Score': scores, 'Name': names, 'Country': countries,
                     'Key-words': keywords, 'Occupation': occupation, 'Bio': bio,
                     'Link': links, 'Social networks': social}

    return speakers_dict


class Speaker:
    def __init__(self, soup):
        self.name = soup.find('h3', {'class': 'speaker-title'}).text.strip()
        self.occupation = soup.find('div', {'class': 'designation'}).text.strip()
        self.country = soup.find('div', {'class': 'country'}).text.strip()
        self.link = soup.find('a', {'class': 'speaker-card-link'}).get('href')
        self.page = load_page(self.link)
        self.keywords = []
        self.score = 0

        self.social_networks = []  # getting social networks
        social_networks = self.page.find('div', {'class': 'speaker-personal-info'}).find_all('a')
        for item in social_networks:
            self.social_networks.append(item.get('href'))

        self.bio = ''
        full_description = self.page.find('div', {'class': 'speaker-about'}).find_all('p')
        for paragraph in full_description:
            self.bio += paragraph.text.strip() + '\n'

    def find_keywords(self, keywords_set, scoring=1, add_keyword=True):
        initial_score = self.score
        occupation_description = '\n'.join([self.bio.lower(), self.occupation.lower()])
        for keyword in keywords_set:
            if keyword in occupation_description:
                self.score += occupation_description.count(keyword) * scoring
                if add_keyword:
                    self.keywords.append(keyword)
        return self.score - initial_score


if __name__ == '__main__':
    speakers_page = load_page(SPEAKERS_URL)
    tag_attr = {'id': 'ajax-list-speaker', 'class': 'list-speakers'}
    speakers_blocks = speakers_page.find('ul', tag_attr).find_all('li')
    number_of_speakers = len(speakers_blocks)
    education_category = []
    others_category = []

    for i, speaker_block in enumerate(speakers_blocks):
        progress = round(((i + 1) / number_of_speakers) * 100, 2)
        print('\r', end='')
        print(str(progress) + '% done', end="", flush=True)
        speaker = Speaker(speaker_block)
        edu_score = speaker.find_keywords(EDU_KEYWORDS)
        other_score = speaker.find_keywords(OTHER_KEYWORDS)
        dropout_score = speaker.find_keywords(DROPOUT_KEYWORDS, scoring=-5, add_keyword=False)

        if speaker.score >= SCORE_PASSING_VAL:
            if edu_score > other_score:
                education_category.append(speaker)
            else:
                others_category.append(speaker)

    edu_df = pd.DataFrame(data=speakers_to_dict(education_category))
    others_df = pd.DataFrame(data=speakers_to_dict(others_category))

    with pd.ExcelWriter('GITEX_speakers.xlsx') as writer:
        edu_df.to_excel(writer, sheet_name='Education')
        others_df.to_excel(writer, sheet_name='Others')
