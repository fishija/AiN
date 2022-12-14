import random
import copy
import pandas as pd
from src.funcitons import to_binary, to_binary_length

from PyQt5.QtCore import pyqtSignal, QObject


class Individual:
    """
    _summary_

    Attributes:
        id (int): Binary individual as decimal number.
        score (int): Total score per individual.
    """
    id = 0
    ind_len = 0
    score = 0
    N = 0
    oponentes_jodidos = 0
    my_choice = None
 
    def __init__(self, prob_of_init_c: float = None, N: int = None, L: int = None, overwrite = None, binary_id: str = None):
        # if binary_id:
        #     binary_id = binary_id.replace(' ', '')
        #     self.ind_len = len(binary_id)
        #     self.N = N
        #     self.id = int(binary_id, 2)

        if not overwrite:
            self.ind_len = '1'
            self.ind_len += to_binary(N-1)
            self.ind_len *= L
            self.ind_len = int(self.ind_len, 2) + 1
            self.N = N

            for i in range(self.ind_len):
                if (random.random() <= prob_of_init_c):
                    self.id += 2**i
        else:
            self.id = overwrite.id
            self.ind_len = overwrite.ind_len
            self.score = overwrite.score
            self.N = overwrite.N
            self.my_choice = overwrite.my_choice
            self.oponentes_jodidos = overwrite.oponentes_jodidos

    def __gt__(self, other):
        if self.score > other.score:
            return True
        return False

    def __lt__(self, other):
        if self.score < other.score:
            return True
        return False

    def choose(self, coop_players_count: list) -> int:
        """
        Attributes:
            coop_players_count (list): History/Prehistory for current individual. Like [[1,3], [1,0], [0,5]] which means - prehistory_l = 3, [[a,b],[a,b]] a = individuals choice, b = how many other individuals cooperated :)
        """
        # [[1,3], [1,0]] -> [[1,011], [1,000]] -> 10111000 -> 184

        decimal_history = ''

        for i in coop_players_count:
            i[1] = to_binary_length(i[1], len(to_binary(self.N-1)))
            decimal_history += ('{a}{b}').format(a = str(i[0]), b = i[1])

        decimal_history = int(decimal_history, 2)

        binary_id = to_binary_length(self.id, self.ind_len)

        self.my_choice = int(binary_id[decimal_history-1])

        return decimal_history

    def count_score(self, coop_players_count, two_pd_payoff_func = None):
        # if 2pPD
        if two_pd_payoff_func:
            if self.my_choice == 0 and coop_players_count[0][1] == 0:
                self.score += two_pd_payoff_func['dd_uno']

            elif self.my_choice == 0 and coop_players_count[0][1] == 1:
                self.score += two_pd_payoff_func['dc_uno']

            elif self.my_choice == 1 and coop_players_count[0][1] == 0:
                self.score += two_pd_payoff_func['cd_uno']

            elif self.my_choice == 1 and coop_players_count[0][1] == 1:
                self.score += two_pd_payoff_func['cc_uno']

        else:
            if self.my_choice == 0:
                self.score += 2 * coop_players_count[0][1] + 1

            elif self.my_choice == 1:
                self.score += (2 * coop_players_count[0][1])

    def mutation (self, mutation_prob: float):
        temp_binary_id = ''
        for current_id_bit in to_binary_length(self.id, self.ind_len):
            if random.random() <= mutation_prob:
                #change current ids bit to opposite
                if current_id_bit == '1':
                    current_id_bit = '0'
                else:
                    current_id_bit = '1'

            temp_binary_id += current_id_bit
        
        self.id = int(temp_binary_id, 2)


class PdTournament:
    """
    Attributes:
        history (list): Like [[0,1,0], [1,0,0], [1,1,1], [0,0,1]]. Which means prehistory_L = 4, players = 3.
    """
    N = 0
    L = 0
    num_of_tournaments = 0
    two_pd_payoff_func = None

    list_of_ind = []
    inds = []
    history = []
    history_count = []

    def __init__(self, list_of_ind, N, L, num_of_tournaments, two_pd_payoff_func: dict = None):
        self.list_of_ind = list_of_ind
        self.N = N
        self.L = L
        self.num_of_tournaments = num_of_tournaments
        self.two_pd_payoff_func = two_pd_payoff_func

        self.history_count = [0] * list_of_ind[0].ind_len

    def update_history(self, last_play: list = None):
        """
        Update history with last play of all players.

        Args:
            last_play (list): Like [0,1,1].
        """
        if last_play:
            self.history.pop()
            self.history.insert(0, last_play)
        else:
            # self.history = [[0,1],[1,0],[0,0]]

            self.history.clear()
            for l in range(self.L):
                temp = []
                for n in range(self.N):
                    if random.random() < 0.5:
                        temp.append(0)
                    else:
                        temp.append(1)

                self.history.append(temp)

    def prep_history_for_individual(self, individual_id: int):
        """
        Return changed history per individual like [[ind_choice, how_many_inds_cooperated], ...]
        """
        to_ret = []

        for i in self.history:
            ind_choice = i[individual_id]

            coop_individuals = 0
            for j in i:
                if j == 1:
                    coop_individuals += 1

            if ind_choice == 1:
                coop_individuals -= 1

            to_ret.append([ind_choice, coop_individuals])

        return to_ret

    def start_whole_tournament(self, num_of_opponents):
        for ind in self.list_of_ind:
            ind.score = 0
            ind.oponentes_jodidos = 0

        for index, ind in enumerate(self.list_of_ind):
            while ind.oponentes_jodidos < num_of_opponents:
                currently_used_inds = [ind]
                for random_selected_ind in random.sample(list(self.list_of_ind[:index] + self.list_of_ind[(index+1):]), k=(self.N-1)):
                    currently_used_inds.append(random_selected_ind)

                self.run_one_tournament(currently_used_inds)

    def run_one_tournament(self, currently_used_inds):
        self.update_history()

        for _ in range(self.num_of_tournaments):
            last_play = []

            for index, cur_ind in enumerate(currently_used_inds):
                self.history_count[cur_ind.choose(self.prep_history_for_individual(index))] += 1
                last_play.append(int(cur_ind.my_choice))

            self.update_history(last_play)

            for index, cur_ind in enumerate(currently_used_inds):
                if self.N > 2:
                    cur_ind.count_score(self.prep_history_for_individual(index))
                else:
                    cur_ind.count_score(self.prep_history_for_individual(index), self.two_pd_payoff_func)

        for cur_ind in currently_used_inds:
            cur_ind.oponentes_jodidos += 1


class Generation:
    """
    _summary_

    Attributes:
        history_count (list): Count for every history that occured in 
    """
    pop_size = 0
    num_of_tournaments = 0
    tournament_size = 0
    crossover_prob = 0
    mutation_prob = 0
    N = 0
    L = 0

    temp_tournament = None

    two_pd_payoff_func = None

    best_individual = None

    list_of_ind = []
    history_count = []

    def __init__(self, pop_size, num_of_tournaments, tournament_size, crossover_prob, prob_of_init_C, N, L, mutation_prob, two_pd_payoff_func: dict = None, list_of_ind: list = None):
        self.pop_size = pop_size
        self.num_of_tournaments = num_of_tournaments
        self.tournament_size = tournament_size
        self.crossover_prob = crossover_prob
        self.two_pd_payoff_func = two_pd_payoff_func
        self.mutation_prob = mutation_prob
        self.N = N
        self.L = L

        self.list_of_ind = list_of_ind

        if not list_of_ind:
            self.list_of_ind = []
            # self.list_of_ind.append(Individual(prob_of_init_C, N, L, binary_id = '0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1'))
            # self.list_of_ind.append(Individual(prob_of_init_C, N, L, binary_id = '0 0 0 0 0 1 1 1 1 1 0 0 0 0 0 1 1 1 1 1 0 0 0 0 0 1 1 1 1 1 0 0 0 0 0 1 1 1 1 1 0 0 0 0 0 1 1 1 1 1 0 0 0 0 0 1 1 1 1 1 0 0 0 0 '))

            for i in range(pop_size):
                self.list_of_ind.append(Individual(prob_of_init_C, N, L))

        self.history_count = [0] * self.list_of_ind[0].ind_len

    def fight_for_death_u_knobs(self, num_of_opponents):
        if self.two_pd_payoff_func:
            self.temp_tournament = PdTournament(self.list_of_ind, self.N, self.L, self.num_of_tournaments, self.two_pd_payoff_func)
        else:
            self.temp_tournament = PdTournament(self.list_of_ind, self.N, self.L, self.num_of_tournaments)

        self.temp_tournament.start_whole_tournament(num_of_opponents)

        self.history_count = [sum(x) for x in zip(self.temp_tournament.history_count, self.history_count)]

    def hard_tournament(self):
        best_ind_list = []

        for i in range(self.pop_size):
            random_chosen_individuals = []
            original_list_index = []

            for j in range(self.tournament_size):
                int_of_ind_to_choose = random.randint(0, self.pop_size - 1)

                if random_chosen_individuals:
                    while int_of_ind_to_choose in original_list_index:
                        int_of_ind_to_choose = random.randint(0, self.pop_size - 1)

                random_chosen_individuals.append(Individual(overwrite = self.list_of_ind[int_of_ind_to_choose]))
                original_list_index.append(int_of_ind_to_choose)

            best_ind_list.append(sorted(random_chosen_individuals, key=lambda x: x.score, reverse=True)[0])

        self.list_of_ind = best_ind_list

    def cross_two_inds(self, ind_uno: Individual, ind_dos: Individual):
        temp_ind_uno = copy.deepcopy(ind_uno)
        temp_ind_dos = copy.deepcopy(ind_dos)

        ind_len = temp_ind_uno.ind_len

        temp_ind_uno_bits = to_binary_length(temp_ind_uno.id, ind_len)
        temp_ind_dos_bits = to_binary_length(temp_ind_dos.id, ind_len)

        chosen_num = random.randint(1, ind_len-1)

        temp_ind_uno.id = int(temp_ind_uno_bits[:chosen_num] + temp_ind_dos_bits[chosen_num:], 2)
        temp_ind_dos.id = int(temp_ind_dos_bits[:chosen_num] + temp_ind_uno_bits[chosen_num:], 2)

        temp_ind_uno.score = 0
        temp_ind_dos.score = 0

        return Individual(overwrite=temp_ind_uno), Individual(overwrite=temp_ind_dos)
        
    def crossover(self):
        self.best_individual = Individual(overwrite = max(self.list_of_ind))

        crossovered_ind_list = []
        
        for ind in self.list_of_ind:
            x = random.random()
            if x > self.crossover_prob:
                self.list_of_ind.remove(ind)
        
        for i in range(0, len(self.list_of_ind), 2):
            ind_uno, ind_dos = None, None

            if i < len(self.list_of_ind) - 1:
                ind_uno, ind_dos = self.cross_two_inds(self.list_of_ind[i], self.list_of_ind[i+1])
            else:
                ind_uno = self.cross_two_inds(self.list_of_ind[i], self.list_of_ind[0])[0]

            if ind_uno:
                crossovered_ind_list.append(Individual(overwrite = ind_uno))
            if ind_dos:
                crossovered_ind_list.append(Individual(overwrite = ind_dos))

        while len(crossovered_ind_list) != self.pop_size:
            chosen_ind_uno, chosen_ind_dos = random.choices(list(self.list_of_ind), k = 2)

            ind_uno, ind_dos= self.cross_two_inds(chosen_ind_uno, chosen_ind_dos)

            if ind_uno:
                crossovered_ind_list.append(Individual(overwrite = ind_uno))
            if ind_dos and len(crossovered_ind_list) != self.pop_size:
                crossovered_ind_list.append(Individual(overwrite = ind_dos))

        self.list_of_ind = crossovered_ind_list

    def mutate_individuals(self):
        for ind in self.list_of_ind:
            ind.mutation(self.mutation_prob)

    def do_elitist(self):
        self.hard_tournament()
        worst_individual = min(self.list_of_ind)
        self.list_of_ind.remove(worst_individual)
        self.list_of_ind.append(Individual(overwrite=self.best_individual))


class GameWorker(QObject):
    is_2_PD = False
    N = 0
    two_pd_payoff_func = dict()
    prob_of_init_C = 0
    num_of_tournaments = 0
    num_of_opponents = 0
    prehistory_L = 0
    pop_size = 0
    num_of_gener = 0
    tournament_size = 0
    crossover_prob = 0
    mutation_prob = 0
    debug = False
    elitist_strategy = False

    history_count = []

    finished = pyqtSignal(pd.DataFrame, list, list)

    def __init__(self, is_2_PD, N, two_pd_payoff_func, prob_of_init_C, num_of_tournaments, num_of_opponents, prehistory_L, pop_size, num_of_gener, tournament_size, crossover_prob, mutation_prob, elitist_strategy, seed, debug, freq_gen_start, delta_freq, canvas_uno, canvas_dos):
        super(GameWorker, self).__init__()

        if is_2_PD:
            self.is_2_PD = is_2_PD
            self.N = 2
        else:
            self.N = N

        self.two_pd_payoff_func = two_pd_payoff_func
        self.prob_of_init_C = prob_of_init_C
        self.num_of_tournaments = num_of_tournaments
        self.num_of_opponents = num_of_opponents
        self.prehistory_L = prehistory_L
        self.pop_size = pop_size
        self.num_of_gener = num_of_gener
        self.tournament_size = tournament_size
        self.crossover_prob = crossover_prob
        self.mutation_prob = mutation_prob
        self.debug = debug
        self.elitist_strategy = elitist_strategy
        self.freq_gen_start = freq_gen_start
        self.delta_freq = delta_freq
        self.canvas_uno = canvas_uno
        self.canvas_dos = canvas_dos

        if seed:
            random.seed(seed)

        
        # self.num_of_tournaments = 5
        # self.num_of_opponents = 1
        # self.pop_size = 2
        # self.num_of_gener = 2
        # self.tournament_size = 2
        # random.seed(1)


    def run(self):
        list_of_ind = []
        avg_data_per_generation = pd.DataFrame(columns=['Avg per Gen', 'Avg per Best'])
        history_count_per_gen = pd.DataFrame()
        whole_history_count = []
        best_individual_ids = []

        for gen in range(1, self.num_of_gener + 1):
            # print('Generation: ', gen)

            if not self.is_2_PD and not list_of_ind:
                curr_generation = Generation(self.pop_size, self.num_of_tournaments, self.tournament_size, self.crossover_prob, self.prob_of_init_C, self.N, self.prehistory_L, self.mutation_prob)
            elif self.is_2_PD and not list_of_ind:
                curr_generation = Generation(self.pop_size, self.num_of_tournaments, self.tournament_size, self.crossover_prob, self.prob_of_init_C, self.N, self.prehistory_L, self.mutation_prob, self.two_pd_payoff_func)
            elif not self.is_2_PD and list_of_ind:
                curr_generation = Generation(self.pop_size, self.num_of_tournaments, self.tournament_size, self.crossover_prob, self.prob_of_init_C, self.N, self.prehistory_L, self.mutation_prob, list_of_ind=list_of_ind)
            else:
                curr_generation = Generation(self.pop_size, self.num_of_tournaments, self.tournament_size, self.crossover_prob, self.prob_of_init_C, self.N, self.prehistory_L, self.mutation_prob, self.two_pd_payoff_func, list_of_ind)

            curr_generation.fight_for_death_u_knobs(self.num_of_opponents)

            sum_of_avg_score_for_gen = 0
            # Count avg scores and all collective oponentes_jodidos
            for ind in curr_generation.list_of_ind:
                ind.score = ind.score/(ind.oponentes_jodidos * self.num_of_tournaments)
                sum_of_avg_score_for_gen += ind.score

            curr_generation.hard_tournament()

            self.history_count = curr_generation.history_count
            h_c_sum = sum(self.history_count)
            for id, h_c in enumerate(self.history_count):
                self.history_count[id] = h_c / h_c_sum
            whole_history_count.append(self.history_count)
            
            curr_generation.crossover()

            best_individual_ids.append(curr_generation.best_individual.id)



            

            # UPDATE UPPER PLOT :)
            avg_data_per_generation.loc[len(avg_data_per_generation) + 1] = [(sum_of_avg_score_for_gen/self.pop_size), (curr_generation.best_individual.score)]
            
            self.canvas_uno.axes.clear()
            self.canvas_uno.fig.set_tight_layout(True)
            self.canvas_uno.axes.set_xlabel('Generations', fontsize=10)
            self.canvas_uno.axes.set_title('Average total payoff', fontsize=14)
            avg_data_per_generation.plot(ax=self.canvas_uno.axes)
            self.canvas_uno.draw()


            # UPDATE LOWER PLOT :)
            if gen == self.freq_gen_start or (gen > self.freq_gen_start and (((gen - self.freq_gen_start) % self.delta_freq) == 0)):
                history_count_per_gen["gen {}".format(gen)] = self.history_count
                # history_count_per_gen.loc[len(history_count_per_gen) + 1] = self.history_count

                self.canvas_dos.axes.clear()
                self.canvas_dos.fig.set_tight_layout(True)
                self.canvas_dos.axes.set_xlabel('Strategies', fontsize=10)
                self.canvas_dos.axes.set_title('Frequencies of applied strategies', fontsize=14)
                history_count_per_gen.plot(ax=self.canvas_dos.axes)
                self.canvas_dos.draw()

            curr_generation.mutate_individuals()


            if self.elitist_strategy:
                curr_generation.do_elitist()

            list_of_ind = curr_generation.list_of_ind

        self.finished.emit(avg_data_per_generation, whole_history_count, best_individual_ids)
