#### RUN THIS TO INSTALL PKGS ########
# This comment indicates that the following line is a shell command to install necessary packages
# python -m pip install semantic-kernel
######################################

# Import necessary packages
import semantic_kernel as sk  # Import the semantic_kernel library
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion  # Import OpenAIChatCompletion from the semantic_kernel library
from semantic_kernel import PromptTemplateConfig, PromptTemplate, SemanticFunctionConfig  # Import additional classes from semantic_kernel
from sklearn.feature_extraction.text import TfidfVectorizer  # Import TfidfVectorizer for text vectorization
from sklearn.metrics.pairwise import cosine_similarity  # Import cosine_similarity for computing similarity between texts
import random  # Import random module for generating random numbers
import time  # Import time module for time-related tasks
import asyncio

# Prepare OpenAI service using credentials stored in the `.env` file
api_key, org_id = sk.openai_settings_from_dot_env()  # Retrieve API key and organization ID from a .env file

# Define a function to calculate cosine similarity between two texts
def calculate_cosine_similarity(text1, text2):
    vectorizer = TfidfVectorizer()  # Initialize a TfidfVectorizer
    tfidf_matrix = vectorizer.fit_transform([text1, text2])  # Transform the texts into TF-IDF matrix
    return cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]  # Return the cosine similarity score

# Define a function to load text lines from a file
def load(filename):
    lines = []  # Initialize an empty list to store lines
    with open(filename, 'r') as file:  # Open the file in read mode
        while True:
            line = file.readline()  # Read a line from the file
            if not line:  # Break the loop if no more lines
                break
            lines.append(line.strip())  # Add the line to the list after stripping whitespace
    return '\n'.join(lines)  # Return the lines joined by newlines

# Define a class to represent a Central Agent
class CentralAgent:
    def __init__(self):
        self.input_text = None  # Initialize input_text attribute to None
        self.kernel = sk.Kernel()  # Initialize a semantic kernel
        self.kernel.add_chat_service("chat-gpt", OpenAIChatCompletion("gpt-3.5-turbo", api_key, org_id))  # Add OpenAI chat service to the kernel

    # Method to upload lecture notes
    def upload_input_text(self, input_text):
        self.input_text = input_text  # Set the input_text attribute

    # Async method to answer a question that the user has posed
    async def answer_question(self, question):
        # Create and execute a semantic function to provide an answer
        return self.kernel.create_semantic_function(f"""Identify whether the user has asked a question in {self.input_text}: Answer it concisely by telling the user of the functionalities you can offer, which include but are not limited to adding any event on the calendar, finding time to do some activity/event, and being able to act as a productivity manager.""", temperature=0.8)()

    # Async method to assign tasks to different Nodes
    async def assign_tasks(self):
        if self.input_text:
            # Create and execute a semantic function to give a lecture transcript
            return self.kernel.create_semantic_function(f"""Break down the tasks that are given in the {self.input_text} and assign them to specific agents based on the functionality and what is supposed to be done with them. Make sure to provide clear instructions to the agents for the specified task""", max_tokens=1024)()
        else:
            throw("No task assigned")  # Throw an error if no question

# Define a class to represent a Node Agent
class NodeAgent:
    def __init__(self, weight):
        self.weight = weight  # Set the weight (e.g., 0.1, 0.2, 0.8)
       
        
        self.kernel = sk.Kernel()  # Initialize a semantic kernel
        self.kernel.add_chat_service("chat-gpt", OpenAIChatCompletion("gpt-4-1106-preview", api_key, org_id))  # Add OpenAI chat service to the kernel

    # Async method to generate questions from a lecture content
    async def generate_questions(self, action):
        new_action = ""  # Initialize a variable to store processed lecture content
        arr = action.split(".") 
        # Process lecture content
        for line in arr:
            r = random.random()  # Generate a random number
            if r < self.retention_rate:
                new_action += line + ".\n"  # Add lines to new content based on retention rate

        action = new_action  # Update lecture content

        # Create and execute a semantic function to generate questions
        return self.kernel.create_semantic_function(f"""You have to perfom a specific action in the calendar defined by:{action}: Pretend that you are an agent who is able to perform actions on the calendar, you have the following abilities {self.educational_background}, and you can ask questions if the instructions are unclear with rate {self.question_rate}. Pretend to be a calendar agent described above who has to perform actions on the personalized google calendar, state one succinct clarifying question you have about the action described and explain to the Central agent which part of the lecture your confusion originated from, and do not state anything other than the question. If you do not want to ask a question respond by saying -1""", max_tokens=200, temperature=0.5)()

    # Method stub for discuss_with_peer (not implemented)
    async def discuss_with_peer(self, peer, action):
        pass  # Placeholder for future implementation




# Define a class to represent a General Agent
class GeneralAgent:
    def __init__(self):
        self.kernel = sk.Kernel()  # Initialize a semantic kernel
        self.kernel.add_chat_service("chat-gpt", OpenAIChatCompletion("gpt-4-1106-preview", api_key, org_id))  # Add OpenAI chat service to the kernel
    
    # Async method to generate a summary of Q&A
    async def generate_summary(self, qa_map):
        # Create and execute a semantic function to generate a summary
        return self.kernel.create_semantic_function(f"""Give a succinct summary of overall and student wise analysis of types, kinds and frequencies of questions asked as per the data in the following map containing questions, answers, and students who asked the questions: {qa_map}.""")()

    async def get_personality(self, myString):
        return self.kernel.create_semantic_function(f"""Give 5 words seperated by commas that describe a student with the following background and retention rates where retention rate describes fraction of information that a student learns from a lecture. {myString}""")()

# Define a coroutine to simulate a lecture session
async def simulate_lecture(lecture, lecture_index, central_agent, node_agent):
    central_agent.upload_input_text(f"""Here are some key points and concepts from lecture {lecture_index + 1} in LateX: {lecture}""")  # Upload lecture notes

    # Simulate classroom interaction
    action = await central_agent.assign_tasks()  # Get the lecture content from the professor
    question_answer_array = []  # Initialize an array to store Q&A pairs

    # Generate questions from all students concurrently
    coroutines = [student.generate_questions(action.result) for student in students]
    all_questions = await asyncio.gather(*coroutines)  # Gather all questions

    prof_coroutines = []  # Initialize an array for professor's responses

    # Process each question and get responses
    for student_index, question in enumerate(all_questions):
        print(question.result)
        if question.result == "-1":  # Check if student doesn't want to ask a question
            continue

        should_ask = True  # Flag to determine if the question should be asked
        for index, [old_question, old_answer, associated_students_list] in enumerate(question_answer_array):
            similarity_threshold = 0.75  # Define a threshold for similarity
            if calculate_cosine_similarity(old_question, question.result) > similarity_threshold:
                should_ask = False  # Set flag to false if similar question already asked
                question_answer_array[index][2].append(student_index)  # Append student index to existing question
                break

        if not should_ask:  # Skip if question should not be asked
            continue

        # Add the professor's response coroutine for the new question
        prof_coroutines.append(professor.answer_question(question.result))
        question_answer_array.append([question.result, "PLACEHOLDER", [student_index]])  # Add new question to the array

    # Gather all responses from the professor
    prof_answers = await asyncio.gather(*prof_coroutines)
    for index in range(len(question_answer_array)):
        question_answer_array[index][1] = prof_answers[index].result  # Update answers in the Q&A array

    # Create a JSON object for the lecture
    qa_map_output = []
    for question, answer, associated_students_list in question_answer_array:
        q_a_pair = {
            "question": question,
            "answer": answer,
            "associated_students_list": associated_students_list
        }
        qa_map_output.append(q_a_pair)  # Append Q&A pairs to the output map

    lecture_Json = {
        "lecture": action.result,
        "QnA": qa_map_output
    }
    return lecture_Json  # Return the lecture JSON object

# Define the main function to simulate a classroom
async def simulate_classroom(content=load("sample.txt")):
    start_time = time.time()  # Record the start time of the simulation

    # Create instances of Central and Node Agents
    central = CentralAgent()  # Instantiate a CentralAgent
    students = [NodeAgent(0.5, "25%", "Can find a specified time block in the calendar"),
                NodeAgent(0.2, "40%", "Can organize a calendar"),
                NodeAgent(0.3, "50%", "political sci"),
                NodeAgent(0.8, "80%", "engineering"),
                NodeAgent(0.8, "99%", "research in statistics")]  # Instantiate a list of StudentAgents with varied profiles

    splitOnSignLectures = "----------"  # Define a delimiter for splitting lecture content
    lectures = content.split(splitOnSignLectures)  # Split the content into individual lectures
    lecture_json_list = []  # Initialize a list to store lecture JSON objects

    qna_json_list = []  # Initialize a list to store Q&A JSON objects
    for lectureIndex, lecture in enumerate(lectures):
        lecture_json = await simulate_lecture(lecture, lectureIndex, professor, students)  # Simulate each lecture
        lecture_json_list.append(lecture_json)  # Append the lecture JSON object to the list
        for q_a_pair in lecture_json["QnA"]:
            qna_json_list.append(q_a_pair)  # Append each Q&A pair to the list

    general_agent = GeneralAgent()  # Instantiate a GeneralAgent
    summary = await general_agent.generate_summary(qna_json_list)  # Generate a summary of Q&A

    # Construct the final JSON object with lecture content and summary
    
    student_list = []
    
    for student in students:
        myString = f"""Background {student.educational_background} ; Retention Rate: {student.retention_rate}"""
        newString = await general_agent.get_personality(myString)
        student_list.append(newString.result)
        
    result_json = {
        "lectures": lecture_json_list,
        "summary": summary.result, # Include the summary in the result
        "students": student_list
    }
    print(result_json)  # Print the result JSON

    end_time = time.time()  # Record the end time of the simulation

    # Calculate and print the elapsed time of the simulation
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time} seconds")
    
    return result_json  # Return the result JSON

# Execute the main function if this script is run as the main module
if __name__ == "__main__":
    import asyncio  # Import asyncio for asynchronous execution
    asyncio.run(simulate_classroom())  # Run the simulate_classroom coroutine
