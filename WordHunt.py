import random, os
from threading import Timer
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

games = {}
timers = {}

TOKEN=''
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher
updater.start_polling()

THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
letter_list_location = os.path.join(THIS_FOLDER, '8letters.txt')

word_list = open(letter_list_location, "r")

line_list = []



for line in word_list:
        line_list.append(line.rstrip('\n').lower())

class GameObject:
    
    def __init__(self):
        global line_list
        self.line_list = line_list
        self.ongoing_game = False
        self.letter_row = []
        self.score_words = []
        self.found_words = []
        self.player_scores = {}
        self.top_score_words = []
        self.player_words = {}

    def create_letter_row(self):
        vowels = ['a','e','i','o','u']
        non_vowels_common = ['b', 'c', 'd', 'f', 'g', 'h', 'k', 'l', 'm', 'n', 'p', 'r', 's', 't','w','y']
        non_vowels_rare = ['j', 'q', 'x', 'z','v']
        num_vowels = random.randint(2,3)
        self.letter_row = []
        for i in range(num_vowels):
            self.letter_row.append(random.choice(vowels))
        for j in range(7 - num_vowels):
            self.letter_row.append(random.choice(non_vowels_common))
        self.letter_row.append(random.choice(non_vowels_rare))
        random.shuffle(self.letter_row)

    def create_score_words(self):
        self.score_words = []
        for word in self.line_list:
            if(self.can_spell(word)):
                self.score_words.append(word)

    def can_spell(self, word):
        word = list(word)
        for letter in self.letter_row:
            if letter in word:
                word.remove(letter)
            if len(word) == 0:
                return True

    def start(self):
        if self.ongoing_game == False:
            self.ongoing_game = True
            while(len(self.score_words) < 125):
                self.create_letter_row()
                self.create_score_words()
            self.top_score_words = sorted(self.score_words, key=len, reverse=True)[0:5]

    def end_clear(self):
        self.letter_row = []
        self.score_words = []
        self.found_words = []
        self.player_scores = {}
        self.top_score_words = []
        self.player_words = {}

    def ongoing_game_false(self):
        self.ongoing_game = False

    def sort_player_words(self):
        for player in self.player_words:
            self.player_words[player] = sorted(self.player_words[player], key=len, reverse=True)


def upper_letters(letter_row):
    upper = ""
    for letter in letter_row:
        upper = upper + " " + letter.upper()
    return upper


def play(update, context):
    global games
    global timers
    chat_id = update.effective_chat.id
    context.bot.send_message(chat_id=chat_id, parse_mode = 'HTML', text="Generating Letters")
    if chat_id not in games:
        games[chat_id] = GameObject()
    games[chat_id].start()

    # Timer control
    timers[chat_id] = Timer(45, end_game, args=[update, context])
    timers[chat_id].start()
    context.bot.send_message(chat_id=chat_id, parse_mode = 'HTML', text=upper_letters(games[chat_id].letter_row))

def scoring(update, context):
    guess = update.message.text
    username = update.effective_user.username
    chat_id = update.effective_chat.id
    if games[chat_id].ongoing_game == True:
        guess = guess.lower()
        print(guess)
        if guess in games[chat_id].found_words:
            found_notif = "<b>{}</b> has already been found!".format(guess)
            context.bot.send_message(chat_id=update.effective_chat.id, parse_mode = 'HTML', text=found_notif)
        elif guess in games[chat_id].score_words:
            score = len(guess) * len(guess)
            notif = "<i>{}</i> found <b>{}</b> for {} points! \n {}".format(username, guess, str(score), upper_letters(games[chat_id].letter_row))
            games[chat_id].score_words.remove(guess)
            games[chat_id].found_words.append(guess)
            if username not in games[chat_id].player_scores:
                games[chat_id].player_scores[username] = 0
            if username not in games[chat_id].player_words:
                games[chat_id].player_words[username] = []
            games[chat_id].player_words[username].append(guess)
            games[chat_id].player_scores[username] = games[chat_id].player_scores[username] + score #create key-value pair in player_scores
            context.bot.send_message(chat_id=update.effective_chat.id, parse_mode = 'HTML', text=notif) #send message saying user has found word

def end_game(update, context):
    chat_id = update.effective_chat.id
    if chat_id in timers:
            timers[chat_id].cancel()
    if games[chat_id].ongoing_game == True:
        games[chat_id].ongoing_game_false()
        context.bot.send_message(chat_id=update.effective_chat.id, parse_mode = 'HTML', text="<b>Game Ended!</b>")
        final_results = "🎉 SCORES: \n"
        for player, score in games[chat_id].player_scores.items():
            final_results = final_results + player + ": " + str(score) + "\n"
        if not bool(games[chat_id].player_scores): # player_scores dict is empty
            final_results = "No one played! \n"
        # Best Possible Words
        final_results += "\n💡 BEST POSSIBLE WORDS: \n"
        for word in games[chat_id].top_score_words:
            final_results += word + "\n"
        # Player Scoring Words
        games[chat_id].sort_player_words()
        final_results += "\n🔎 WORDS FOUND \n"
        for player in games[chat_id].player_words:
            final_results += "<b>" + player + "("+str(len(games[chat_id].player_words[player]))+")</b> \n"
            for word in games[chat_id].player_words[player]:
                final_results += word + " "
            final_results += "\n"
        context.bot.send_message(chat_id=update.effective_chat.id, parse_mode = 'HTML', text=final_results)
        games[chat_id].end_clear()

def help(update, context):
    helptext = """<b> Word Hunt </b>
    Try to score the most points by forming words from the letters given and typing them into the chat.
    
    Each letter that appears in the letter row can only be used once. <i>(e.g. If 'G' appears once, it can only be used once per word, but if 'G' appears twice it can be used twice in the word.)</i>

    Once a word has been scored, other players will not score points by typing the word.

    The points awarded for each word is equal to the length of the word squared.

    Each game lasts for 45 seconds.

    /play - Starts a game.
    /end - Ends a game.
    /help - Help message.
    """
    context.bot.send_message(chat_id=update.effective_chat.id, parse_mode = 'HTML', text=helptext)
        

play_handler = CommandHandler('play_word', play)
updater.dispatcher.add_handler(play_handler)

end_handler = CommandHandler('end', end_game)
updater.dispatcher.add_handler(end_handler)

help_handler = CommandHandler('help', help)
updater.dispatcher.add_handler(help_handler)

message_handler = MessageHandler(Filters.text & (~Filters.command), scoring)
updater.dispatcher.add_handler(message_handler)





