import streamlit as st
from newspaper import Article
from konlpy.tag import Okt
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import requests
from bs4 import BeautifulSoup
import re

# matplotlib의 Agg 모드 설정
plt.switch_backend('Agg')

# Konlpy의 Okt 객체를 미리 생성합니다.
okt = Okt()

def fetch_news_content(url, stop_words):
    try:
        article = Article(url, language='ko')
        article.download()
        article.parse()
    except Exception as e:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            content = soup.find('div', class_=re.compile(r'(content|article|post|text|article_body|main_content|article_txt|article_view)'))
            if not content:
                content = soup
            text = ' '.join(content.stripped_strings)
            title = soup.title.string if soup.title else "제목 없음"
        else:
            return "오류: 웹사이트에 접근할 수 없습니다.", ""
    else:
        title = article.title
        text = article.text
    
    text = preprocess_text(text, stop_words)
    return title, text

def preprocess_text(text, stop_words):
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = ' '.join(word for word in text.split() if word not in stop_words)
    return text.strip()

def word_frequency_analysis(text):
    # 명사 추출 및 빈도수 계산
    nouns = okt.nouns(text)
    nouns = [noun for noun in nouns if len(noun) > 1]  # 한 글자 명사 제외
    count = Counter(nouns)
    return count

# display_wordcloud 및 display_bar_chart 함수는 이전과 동일합니다.
def display_wordcloud(word_counts):
    # 워드 클라우드 생성 및 표시
    wordcloud = WordCloud(width=800, height=400, background_color='white', font_path='NanumBarunGothic.ttf').generate_from_frequencies(word_counts)
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    st.pyplot(plt)

def display_bar_chart(word_counts):
    # 바 차트 생성 및 표시
    words, frequencies = zip(*word_counts)  # 단어와 빈도수 분리
    plt.figure(figsize=(10, 5))
    plt.bar(words, frequencies)
    plt.xlabel('Words')
    plt.ylabel('Frequency')
    plt.xticks(rotation=45)
    st.pyplot(plt)

st.title('뉴스 콘텐츠 분석기')

num_links = st.number_input('분석할 링크 수를 입력하세요', min_value=1, value=1, step=1, key='num_links')
urls = []
stop_words_list = []

for i in range(num_links):
    urls.append(st.text_input(f'링크 {i+1}', key=f'url_{i}'))
    stop_words_input = st.text_input(f'링크 {i+1}에 대한 중지어 (공백으로 구분)', key=f'stopwords_{i}', placeholder="예: 기사 댓글 바로가기")
    stop_words_list.append(set(stop_words_input.split()))

if st.button('분석 시작'):
    for i, url in enumerate(urls):
        if url:
            with st.spinner(f"{url}에서 데이터를 가져오는 중..."):
                title, text = fetch_news_content(url, stop_words_list[i])
                if title.startswith("오류"):
                    st.error(text)
                else:
                    word_counts = word_frequency_analysis(text)
                    st.write(f"### {title}")
                    st.write("가장 많이 사용된 단어 Top 20:")
                    word_dict = dict(word_counts.most_common(20))
                    st.json(word_dict)
                    display_wordcloud(word_counts)
                    display_bar_chart(word_counts.most_common(10))
