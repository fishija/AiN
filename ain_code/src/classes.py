import random
import copy
from src.funcitons import to_binary, to_binary_length


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
    my_choice = None
 
    def __init__(self, prob_of_init_c: float, N: int, L: int):
        self.ind_len = '1'
        self.ind_len += to_binary(N-1)
        self.ind_len *= L
        self.ind_len = int(self.ind_len, 2) + 1
        self.N = N

        for i in range(self.ind_len):
            if (random.random() <= prob_of_init_c):
                self.id += 2**i

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

        self.my_choice = binary_id[decimal_history]

        return decimal_history

    def count_score(self, coop_players_count, two_pd_payoff_func = None):
        # if 2pPD
        if two_pd_payoff_func:
            if self.my_choice == 0 and coop_players_count == 0:
                self.score += two_pd_payoff_func['dd_uno']

            elif self.my_choice == 0 and coop_players_count == 1:
                self.score += two_pd_payoff_func['dc_uno']

            elif self.my_choice == 1 and coop_players_count == 0:
                self.score += two_pd_payoff_func['cd_uno']

            elif self.my_choice == 1 and coop_players_count == 1:
                self.score += two_pd_payoff_func['cc_uno']

        else:
            if self.my_choice == 0:
                self.score += 2 * coop_players_count + 1

            elif self.my_choice == 1:
                self.score += (2 * coop_players_count)

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

    def start_whole_tournament(self):
        print('Whole tournament started')
        for ind in self.list_of_ind:
            self.run_one_tournament(ind)

    def run_one_tournament(self, ind: Individual):
        self.update_history()
        self.currently_used_inds = []

        self.currently_used_inds.append(dict(individual = ind, number = 0))

        temp_individuals = copy.copy(self.list_of_ind) #####################################

        temp_individuals.remove(ind)

        # print(list(set(self.list_of_ind) - set(temp_individuals)))

        for n in range(1, self.N):
            temp = random.randint(0, len(temp_individuals)-1)
            self.currently_used_inds.append(dict(individual = temp_individuals[temp], number = n))
            del temp_individuals[temp]

        for i in range(self.num_of_tournaments):
            last_play = []

            for ind_dictionary in self.currently_used_inds:
                self.history_count[ind_dictionary['individual'].choose(self.prep_history_for_individual(ind_dictionary['number']))] += 1
                last_play.append(int(ind_dictionary['individual'].my_choice))

            self.update_history(last_play)

            for ind_dictionary in self.currently_used_inds:
                if self.N > 2:
                    ind_dictionary['individual'].count_score(self.prep_history_for_individual( ind_dictionary['number']))
                else:
                    ind_dictionary['individual'].count_score(self.prep_history_for_individual( ind_dictionary['number']), self.two_pd_payoff_func)

        for ind_dictionary in self.currently_used_inds:
            self.list_of_ind[ind_dictionary['number']].score = ind_dictionary['individual'].score

    def end_tournament(self):
        return self.list_of_ind


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

        if list_of_ind:
            self.list_of_ind = list_of_ind
        else:
            for i in range(pop_size):
                self.list_of_ind.append(Individual(prob_of_init_C, N, L))

        self.history_count = [0] * self.list_of_ind[0].ind_len

    def fight_for_death_u_knobs(self):
        if self.two_pd_payoff_func:
            self.temp_tournament = PdTournament(self.list_of_ind, self.N, self.L, self.num_of_tournaments, self.two_pd_payoff_func)
        else:
            self.temp_tournament = PdTournament(self.list_of_ind, self.N, self.L, self.num_of_tournaments)

        self.temp_tournament.start_whole_tournament()

        self.history_count = [sum(x) for x in zip(self.temp_tournament.history_count, self.history_count)]
        self.list_of_ind = self.temp_tournament.end_tournament()

    def hard_tournament(self):
        best_ind_list = []

        for ind in self.list_of_ind:
            ind.score = 0

        for i in range(self.pop_size):
            random_chosen_individuals = []

            for j in range(self.tournament_size):
                temp_ind = self.list_of_ind[random.randint(0, self.pop_size - 1)]

                while temp_ind in random_chosen_individuals:
                    temp_ind = self.list_of_ind[random.randint(0, self.pop_size - 1)]

                random_chosen_individuals.append(temp_ind)

            best_ind_list.append(sorted(random_chosen_individuals, key=lambda x: x.score, reverse=True)[0])

        self.list_of_ind = best_ind_list

    def cross_two_inds(self, ind_uno: Individual, ind_dos: Individual):
        ind_len = ind_uno.ind_len

        ind_uno_bits = to_binary_length(ind_uno.id, ind_len)
        ind_dos_bits = to_binary_length(ind_dos.id, ind_len)

        chosen_num = random.randint(1, ind_len-1)

        ind_uno.id = int(ind_uno_bits[:chosen_num] + ind_dos_bits[chosen_num:], 2)
        ind_dos.id = int(ind_dos_bits[:chosen_num] + ind_uno_bits[chosen_num:], 2)

        return ind_uno, ind_dos
        
    def crossover(self):

        


        self.best_individual = max(self.list_of_ind)
        print('Best individual id: ', to_binary_length(self.best_individual.id, self.best_individual.ind_len))
        crossovered_ind_list = []
        
        for ind in self.list_of_ind:
            if random.random() > self.crossover_prob:
                self.list_of_ind.remove(ind)
        
        for i in range(0, len(self.list_of_ind), 2):
            ind_uno, ind_dos = None, None

            if i < len(self.list_of_ind) - 1:
                ind_uno, ind_dos = self.cross_two_inds(self.list_of_ind[i], self.list_of_ind[i+1])
            else:
                ind_uno = self.cross_two_inds(self.list_of_ind[i], self.list_of_ind[0])[0]

            if ind_uno:
                crossovered_ind_list.append(ind_uno)
            if ind_dos:
                crossovered_ind_list.append(ind_dos)

        while len(crossovered_ind_list) != self.pop_size:
            chosen_ind_uno, chosen_ind_dos = random.choices(list(set(self.list_of_ind)), k = 2)
            ind_uno, ind_dos= self.cross_two_inds(chosen_ind_uno, chosen_ind_dos)

            if ind_uno:
                crossovered_ind_list.append(ind_uno)
            if ind_dos and len(crossovered_ind_list) != self.pop_size:
                crossovered_ind_list.append(ind_dos)

        self.list_of_ind = crossovered_ind_list

    def mutate_individuals(self):
        for ind in self.list_of_ind:
            ind.mutation(self.mutation_prob)

    def do_elitist(self):
        self.hard_tournament()
        worst_individual = min(self.list_of_ind)
        self.list_of_ind.remove(worst_individual)
        self.list_of_ind.append(self.best_individual)


class Game:
    """
    _summary_
    """
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

    def __init__(self, is_2_PD, N, two_pd_payoff_func, prob_of_init_C, num_of_tournaments, num_of_opponents, prehistory_L, pop_size, num_of_gener, tournament_size, crossover_prob, mutation_prob, elitist_strategy, seed, debug):
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

        if seed:
            random.seed(seed)

    def play(self):
        list_of_ind = []

        for i in range(self.num_of_gener):
            print('Generacion: ', i)

            if not self.is_2_PD and not list_of_ind:
                old_generation = Generation(self.pop_size, self.num_of_tournaments, self.tournament_size, self.crossover_prob, self.prob_of_init_C, self.N, self.prehistory_L, self.mutation_prob)
            elif self.is_2_PD and not list_of_ind:
                old_generation = Generation(self.pop_size, self.num_of_tournaments, self.tournament_size, self.crossover_prob, self.prob_of_init_C, self.N, self.prehistory_L, self.mutation_prob, self.two_pd_payoff_func)
            elif not list_of_ind:
                old_generation = Generation(self.pop_size, self.num_of_tournaments, self.tournament_size, self.crossover_prob, self.prob_of_init_C, self.N, self.prehistory_L, self.mutation_prob, list_of_ind)
            else:
                old_generation = Generation(self.pop_size, self.num_of_tournaments, self.tournament_size, self.crossover_prob, self.prob_of_init_C, self.N, self.prehistory_L, self.mutation_prob, self.two_pd_payoff_func, list_of_ind)

            old_generation.fight_for_death_u_knobs()
            old_generation.hard_tournament()
            self.history_count = old_generation.history_count #######################################################################################################################################################################################
            old_generation.crossover()
            old_generation.mutate_individuals()

            if self.elitist_strategy:
                old_generation.do_elitist()

            list_of_ind = old_generation.list_of_ind


        print(self.history_count)
            
        # create chart -- either at the end or in create generations loop
