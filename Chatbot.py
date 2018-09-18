from textblob import TextBlob
#from attributegetter import *
from generatengrams import ngrammatch
from Contexts import *
import json
from Intents import *
import random
import os
import re
import pandas as pd

def check_actions(current_intent, attributes, context):
    '''This function performs the action for the intent
    as mentioned in the intent config file
    Performs actions pertaining to current intent '''
    '''for action in current_intent.action:
        if action.contexts_satisfied(active_contexts):
            return perform_action()'''
    #print(current_intent.name)
    #print(attributes)
    if current_intent.name == 'Restaurant':
        #print('rest')
        lst = [attributes['costType'],attributes['cuisine'],attributes['restLocation']]
        lst = [element.lower() for element in lst]
        df = pd.read_csv('restaurants.csv')
        x = df.query("costType==@lst[0] and cuisine==@lst[1] and location == @lst[2]")
        context = IntentComplete()
        rest = x['Restaurant'].values
        return 'Table booked in : ' +rest , context
    elif current_intent.name == 'LibraryBook':
        #print('lib')
        lst = [attributes['subject'],attributes['title'],attributes['author']]
        lst = [element.lower() for element in lst]
        df = pd.read_csv('books.csv')
        x = df.query("subject==@lst[0] and title==@lst[1] and author == @lst[2]")
        context = IntentComplete()
        rack = x['rack'].values
        return 'Pick the book from ' +rack , context
    

def check_required_params(current_intent, attributes, context):
    '''Collects attributes pertaining to the current intent'''
    
    for para in current_intent.params:
        if para.required:
            if para.name not in attributes:
                if para.name=='RegNo':
                    context = GetRegNo()
                return random.choice(para.prompts), context

    return None, context


def input_processor(user_input, context, attributes, intent):
    '''Spellcheck and entity extraction functions go here'''
    
    uinput = TextBlob(user_input).correct().string
    
    #update the attributes, abstract over the entities in user input
    attributes, cleaned_input = getattributes(user_input, context, attributes)
    #print(cleaned_input)
    return attributes, cleaned_input

def loadIntent(path, intent):
    with open(path) as fil:
        dat = json.load(fil)
        intent = dat[intent]
        #print(intent)
        return Intent(intent['intentname'],intent['Parameters'], intent['actions'])

def intentIdentifier(clean_input, context,current_intent):
    clean_input = clean_input.lower()
    scores = ngrammatch(clean_input)
    scores = sorted_by_second = sorted(scores, key=lambda tup: tup[1])
    #print (clean_input)
    #print ('scores', scores)
    
    if(current_intent==None):
        '''if(clean_input=="search"):
            return loadIntent('params/skills_team31.cfg', 'SearchStore')'''
        if(clean_input=='book'):
            return loadIntent('params/skills_team31.cfg','LibraryBook')
        if(clean_input=='restaurant'):
            return loadIntent('params/skills_team31.cfg','Restaurant')
        else:
            return loadIntent('params/skills_team31.cfg',scores[-1][0])
    else:
        #print 'same intent'
        return current_intent

def getattributes(uinput,context,attributes):
    '''This function marks the entities in user input, and updates
    the attributes dictionary'''
    #Can use context to to context specific attribute fetching
    #print('uinput',uinput)
    if context.name.startswith('IntentComplete'):
        return attributes, uinput
    else:

        files = os.listdir('./entities/')
        entities = {}
        for fil in files:
            lines = open('./entities/'+fil).readlines()
            for i, line in enumerate(lines):
                lines[i] = line[:-1]
            entities[fil[:-4]] = '|'.join(lines)

        #Extract entity and update it in attributes dict
        
        for entity in entities:
            for i in entities[entity].split('|'):
                if i.lower() in uinput.lower():
                    attributes[entity] = i
        for entity in entities:
            uinput = re.sub(entities[entity],r'$'+entity,uinput,flags=re.IGNORECASE)

        #Example of where the context is being used to do conditional branching.
        if context.name=='GetRegNo' and context.active:
            print(attributes)
            match = re.search('[0-9]+', uinput)
            if match:
                uinput = re.sub('[0-9]+', '$regno', uinput)
                attributes['RegNo'] = match.group()
                context.active = False

        return attributes, uinput
#re.sub('wings of fire',r'$'+'title','wings of fire',flags=re.IGNORECASE)

class Session:
    def __init__(self, attributes=None, active_contexts=[FirstGreeting(), IntentComplete()]):
        
        '''Initialise a default session'''
        
        #Contexts are flags which control dialogue flow, see Contexts.py
        self.active_contexts = active_contexts
        self.context = FirstGreeting()
        
        #Intent tracks the current state of dialogue
        #self.current_intent = First_Greeting()
        self.current_intent = None
        
        #attributes hold the information collected over the conversation
        self.attributes = {}
        
    def update_contexts(self):
        '''Not used yet, but is intended to maintain active contexts'''
        for context in self.active_contexts:
            if context.active:
                context.decrease_lifespan()
                
    
    def reply(self, user_input):
        
        #print('userinput: ',user_input)
        
        '''Generate response to user input'''
        self.attributes, clean_input = input_processor(user_input, self.context, self.attributes, self.current_intent)
        
        self.current_intent = intentIdentifier(clean_input, self.context, self.current_intent)
        
        prompt, self.context = check_required_params(self.current_intent, self.attributes, self.context)

        #prompt being None means all parameters satisfied, perform the intent action
        if prompt is None:
            if self.context.name!='IntentComplete':
                prompt, self.context = check_actions(self.current_intent, self.attributes, self.context)
        
        
        #Resets the state after the Intent is complete
        if self.context.name=='IntentComplete':
            self.attributes = {}
            self.context = FirstGreeting()
            self.current_intent = None
            
        
        return prompt,self.context

session = Session()

print ('BOT: Hi! How may I assist you?')

while True:
    
    inp = input('User: ')
    prompt,session.context = session.reply(inp)
    if session.context.name== 'FirstGreeting' and inp in ['bye','off','sleep','thank you']:
        print('Thank you!! Prompt if you need me')
        print('Bye')
        break
    elif inp == 'restart':
        session = Session()
        print ('Okay!! Lets start over again.')
        
    else:
        print ('BOT:', prompt)

