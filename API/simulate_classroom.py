#### RUN THIS TO INSTALL PKGS ########
# python -m pip install semantic-kernel
######################################

# Import necessary packages
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel import PromptTemplateConfig, PromptTemplate, SemanticFunctionConfig
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import random


# Prepare OpenAI service using credentials stored in the `.env` file
api_key, org_id = sk.openai_settings_from_dot_env()


# Cosine Similarity Function
def calculate_cosine_similarity(text1, text2):
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([text1, text2])
    return cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]


# Load x lines from a file
def load(filename, lines_to_read = 50):
    lines = []
    with open(filename, 'r') as file:
        for _ in range(lines_to_read):
            line = file.readline()
            if not line:
                break
            lines.append(line.strip())

    return '\n'.join(lines)




# Define prompts
class ProfessorAgent:
    def __init__(self):
        self.lecture_notes = None
        self.kernel = sk.Kernel()
        self.kernel.add_chat_service("chat-gpt", OpenAIChatCompletion("gpt-3.5-turbo-16k", api_key, org_id))

    def upload_lecture_notes(self, notes):
        self.lecture_notes = notes

    async def answer_question(self, question):
        return self.kernel.create_semantic_function(f"""Provide a detailed answer to the following question received after the following lecture {self.lecture_notes}: {question}? Answer concisely.""", temperature=0.8)()

    async def give_lecture(self):
        if self.lecture_notes:
            # Incorporating lecture notes into the lecture generation
            return self.kernel.create_semantic_function(f"""Give a transcript of a detailed lecture (just the first 5 minutes (around 250 words)), using the following notes in LaTeX, with approporiate fillers to make the lecture engaging: {self.lecture_notes}.""", max_tokens=1024)()
        else:
            throw("No lecture notes uploaded")

class StudentAgent:
    def __init__(self, retention_rate, question_rate, educational_background):
        self.retention_rate = retention_rate # 0.1, 0.2, 0.8
        self.question_rate = question_rate # 0.1, 0.2, 0.8
        self.educational_background = educational_background # Liberal Arts, Engineering, Pure Researcher
        
        #initialize kernel
        self.kernel = sk.Kernel()
        self.kernel.add_chat_service("chat-gpt", OpenAIChatCompletion("gpt-3.5-turbo", api_key, org_id))


    async def generate_questions(self, lecture_content):
        new_lecture_content = ""
        arr = lecture_content.split(".")
        for line in arr:
            r = random.random()
            if r < self.retention_rate:
                new_lecture_content += line + ".\n"
        lecture_content = new_lecture_content


        return self.kernel.create_semantic_function(f"""As a student, you went through the following {lecture_content}: Pretend that you are a student with educational background of {self.educational_background}, and have likelihood to ask question of {self.question_rate}. Pretend to be the student described above learning from this lecture, state one clarifying question you have about this lecture, and do not state anything other than the question. If you do not want to ask a question respond by saying -1""",max_tokens=120,temperature=0.5)()

    async def discuss_with_peer(self, peer, lecture_content):
        # This function simulates discussion between two students
        pass

class GeneralAgent:
    def __init__(self):
        self.kernel = sk.Kernel()
        self.kernel.add_chat_service("chat-gpt", OpenAIChatCompletion("gpt-3.5-turbo", api_key, org_id))
    
    async def generate_summary(self, qa_map):
        return self.kernel.create_semantic_function(f"""Give a detailed summary of overall and student wise analysis of types, kinds and frequencies of questions asked as per the data in the following map containing questions, answers, and students who asked the questions: {qa_map}.""")()

'''
Returns a Json Object 
'''
async def simulate_lecture(lecture, lecture_index, professor, students):
    professor.upload_lecture_notes(f"""Here are some key points and concepts from lecture {lecture_index + 1} in LateX: {lecture}""")

    # Simulate classroom interaction
    lecture_content = await professor.give_lecture()
    # print(lecture_content)
    question_answer_array = []
    # print("Question + Answer pairs: ")

    for student_index, student in enumerate(students):
        question = await student.generate_questions(lecture_content.result)
        print(question.result)
        if question.result == "-1":
            continue

        should_ask = True
        for index, [old_question, old_answer, associated_students_list] in enumerate(question_answer_array):
            similarity_threshold = 0.75  # Adjust the threshold as needed
            if calculate_cosine_similarity(old_question, question.result) > similarity_threshold:
                should_ask = False
                question_answer_array[index][2].append(student_index)
                break

        if not should_ask:
            continue

        answer = await professor.answer_question(question.result)
        question_answer_array.append([question.result, answer.result, [student_index]])
        # print("Question: ", question.result)
        # print("Answer: ", answer.result)

    # print(len(question_answer_array))
    # for index, [question, answer, associated_students_list] in enumerate(question_answer_array):
    #     print(f"""Index: {index}, Student {associated_students_list}""")
    #
    # Modify the final Q-A map output structure
    qa_map_output = []
    for question, answer, associated_students_list in question_answer_array:
        q_a_pair = {
            "question": question,
            "answer": answer,
            "associated_students_list": associated_students_list
        }
        qa_map_output.append(q_a_pair)

    lecture_Json = {
        "lecture": lecture_content.result,
        "QnA": qa_map_output
    }
    return lecture_Json


async def runQuiz():


# Main simulation function
async def simulate_classroom(content=load("lecture-notes.txt")):

    # Create Professor and Student Agents
    professor = ProfessorAgent("Mathematics")
    students = [StudentAgent(0.5, 0.7, "really smart liberal arts students studying anthropology"),
                StudentAgent(0.8, 0.3, "engineering"),
                StudentAgent(0.95, 0.95, "research in math"),
                StudentAgent(0.7, 0.3, "physics"),
                StudentAgent(0.2, 0.2, "art history"),
                StudentAgent(0.3, 0.4, "political science"),
                StudentAgent(0.8, 0.5, "engineering"),
                StudentAgent(0.8, 0.99, "research in statistics")]

    splitOnSignQuizzes = "=========="
    lecturesString, quizzes = content.split(splitOnSign)

    splitOnSignLectures = "----------"
    lectures = lecturesString.split(splitOnSignLectures)
    lecture_json_list = []
    for lectureIndex, lecture in enumerate(lectures):
        lecture_json_list.append(await simulate_lecture(lecture, lectureIndex, professor, students))

    general_agent = GeneralAgent()
    summary = await general_agent.generate_summary(lecture_json_list)
    # Add lecture content and summary
    result_json = {
        "lectures": lecture_json_list,
        "summary": summary.result  # Replace with an actual summary if available
    }
    print(result_json)
    return result_json


# Run the main function
if __name__ == "__main__":
    import asyncio
    asyncio.run(simulate_classroom())