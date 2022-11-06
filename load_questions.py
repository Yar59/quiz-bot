import argparse
import os
import pathlib
import random
import json


def load_questions_from_files(questions_dir):
    questions_answers = {}
    for question_file in os.listdir(questions_dir):
        print(f'Загружаю вопросы из файла {question_file}')
        question_path = os.path.join(questions_dir, question_file)
        with open(question_path, 'r', encoding='KOI8-R') as file:
            file_content = file.read()
        splited_file = file_content.split('\n\n')[4:]
        questions = []
        answers = []
        for part in splited_file:
            sentence = (part.replace('\n', '', 1)).replace('\n', ' ')
            if sentence.startswith('Вопрос'):
                questions.append(' '.join(sentence.split(':')[1:]))
            elif sentence.startswith('Ответ'):
                answers.append(' '.join(sentence.split(':')[1:]))

        compilation = dict(zip(questions, answers))
        questions_answers.update(compilation)
    return questions_answers


def load_questions_answers(file_path):
    with open(file_path, 'rb') as file:
        return json.load(file)


def get_random_question(questions_answers):
    return random.choice(list(questions_answers.keys()))


def main():
    parser = argparse.ArgumentParser(description='Загрузка и сохранение вопросов и ответов для викторины')
    parser.add_argument('load_dir', type=pathlib.Path, help='Директория с файлами вопросов')
    parser.add_argument('--save_json', type=pathlib.Path, help='Сохранить вопросы в json файл')

    args = parser.parse_args()
    questions_answers = load_questions_from_files(args.load_dir)
    if args.save_json:
        with open(args.save_json, 'w') as file:
            json.dump(questions_answers, file)


if __name__ == '__main__':
    main()
