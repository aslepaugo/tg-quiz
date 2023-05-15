
def open_quiz(filename):
    with open(filename, 'r', encoding='KOI8-R') as f:
        text = f.read()
    text = text.split('\n\n')
    question = ''
    answer = ''
    quiz = {}
    for line in text:
        if line.strip().startswith('Вопрос'):
            question = line.strip().split('\n', maxsplit=1)[1].replace('\n', ' ')
        elif line.startswith('Ответ'):
            answer = line.strip().split('\n', maxsplit=1)[1].replace('\n', ' ')

        if question and answer:
            quiz[question] = answer
            question = ''
            answer = ''

    return quiz


def main():
    quiz = open_quiz('./quiz-questions/1vs1200.txt')
    print(quiz)


if __name__ == '__main__':
    main()
