# Mishukov Konstantin
# 2021

import os
import getopt
from multiprocessing import *
import sys
import time
from typing import Optional
import multiprocessing
from myQueue import Queue

import numpy as np

# main.py -i m.txt

path = ''
try:
    opts, args = getopt.getopt(sys.argv[1:], "hi:", ["ifile="])
except getopt.GetoptError:
    print('main.py -i <inputfile>')
    sys.exit(2)
for opt, arg in opts:
    if opt == '-h':
        print('main.py -i <inputfile>')
        sys.exit()
    elif opt in ("-i", "--ifile"):
        path = arg

if path == "":
    print('Missing parameters.')
    print('main.py -i <inputfile>')
    sys.exit(2)


def parsefile(filepath):
    try:
        mtx = np.loadtxt(filepath, dtype='int')
        print('Input Matrix:\n', mtx)
        return mtx
    except IOError:
        print("Error: file could not be opened")
        sys.exit(2)


matrix = parsefile(path)
matrix_size: int = len(matrix)

maxsize = float('inf')
# best_solution_record = float('inf')
best_solution = None
solutions_queue = Queue()


# Calculate lower bound on any given solution (step);
def calculate_bound(solution) -> float:
    summary = 0
    for i in range(matrix_size):
        first_minimum = float('inf')
        second_minimum = float('inf')
        for j in range(matrix_size):
            current_branch = Branch(i, j)
            if i == j or solution.branches[current_branch] is False:
                continue
            if matrix[i][j] <= first_minimum:
                second_minimum = first_minimum
                first_minimum = matrix[i][j]
            elif matrix[i][j] < second_minimum:
                second_minimum = matrix[i][j]
        summary += first_minimum + second_minimum
    return summary * 0.5


def make_branches(solution, flag, sharedQueue, best_solution_record):
    # flag.value += 1
    global best_solution
    if solution.number_of_included_branches() >= matrix_size - 2:
        include_branches_if_needed(solution)
        solution_total_bound = solution.current_bound()
        # print("Tree finished:", solution_total_bound)
        if solution_total_bound < best_solution_record.value:
            with best_solution_record.get_lock():
                best_solution_record.value = solution.current_bound()
            best_solution = solution
            print('Record updated:', best_solution_record.value, 'Process:', multiprocessing.current_process())
        # flag.value -= 1
        return

    for i in range(matrix_size):
        if solution.has_two_adjacents_to_node(i):
            continue
        for j in range(matrix_size):
            if i == j:
                continue
            current_branch = Branch(i, j)
            if current_branch in solution.branches.keys():
                continue

            new_solution1 = Solution()
            new_solution1.branches = solution.branches.copy()
            new_solution1.branches[current_branch] = True
            new_solution1.update_solution_with_missing_branches_if_needed(current_branch)

            new_solution2 = Solution()
            new_solution2.branches = solution.branches.copy()
            new_solution2.branches[current_branch] = False
            new_solution2.update_solution_with_missing_branches_if_needed(None)

            s1_bound = new_solution1.current_bound()
            if s1_bound <= best_solution_record.value and new_solution1.impossible is False:
                sharedQueue.put(new_solution1)
            # else:
            #     if new_solution1.impossible is True:
            #         print('Impossible solution, pruned.')
            #     else:
            #         print('Solution pruned: ', best_solution_record, "<", new_solution1.current_bound())
            s2_bound = new_solution2.current_bound()
            if s2_bound <= best_solution_record.value and new_solution2.impossible is False:
                sharedQueue.put(new_solution2)
            # else:
            #     if new_solution2.impossible is True:
            #         print('Impossible solution, pruned.')
            #     else:
            #         print('Solution pruned: ', best_solution_record, "<", new_solution2.current_bound())
            # flag.value -= 1
            # print('Exit 1:', flag.value)
            return

    # print('Exit 2', flag)
    # flag.value -= 1

class Branch:
    def __init__(self, node_a, node_b):
        if node_a > node_b:
            self.nodeA = node_b
            self.nodeB = node_a
        else:
            self.nodeA = node_a
            self.nodeB = node_b

    def __eq__(self, other):
        if isinstance(other, Branch):
            return (self.nodeA == other.nodeA and self.nodeB == other.nodeB) or (
                        self.nodeA == other.nodeB and self.nodeB == other.nodeA)
        return False

    def __hash__(self):
        if self.nodeA < self.nodeB:
            return hash((self.nodeA, self.nodeB))
        else:
            return hash((self.nodeB, self.nodeA))

    def __ne__(self, other):
        return not (self == other)

    def __str__(self):
        return '(' + str(self.nodeA) + ', ' + str(self.nodeB) + ')'

    def is_incident_to(self, node):
        return self.nodeA == node or self.nodeB == node


class Solution:
    def __init__(self):
        self.impossible = False
        self.branches = dict()

    def current_bound(self):
        summary = 0
        for i in range(matrix_size):
            first_minimum = float('inf')
            second_minimum = float('inf')
            for j in range(matrix_size):
                current_branch = Branch(i, j)
                if i == j or self.branches.get(current_branch) is False:
                    continue
                if matrix[i][j] <= first_minimum:
                    second_minimum = first_minimum
                    first_minimum = matrix[i][j]
                elif matrix[i][j] < second_minimum:
                    second_minimum = matrix[i][j]
            summary += first_minimum + second_minimum
        return summary * 0.5

    def has_two_adjacents_to_node(self, node):
        adjacents_counter = 0
        for branch in self.branches.keys():
            if branch.is_incident_to(node) and self.branches[branch] is True:
                adjacents_counter += 1
                if adjacents_counter == 2:
                    return True
        return False

    def number_of_included_branches(self):
        number = 0
        for k in self.branches.keys():
            if self.branches[k] is True:
                number += 1
        return number

    def print_solution(self):
        if self.number_of_included_branches() != matrix_size:
            print('Error: tried printing not complete solution.')
            return
        path = '0'
        zero_branches = []
        true_branches = []
        for branch in self.branches.keys():
            if self.branches[branch] is True:
                true_branches.append(branch)
        for branch in true_branches:
            if branch.is_incident_to(0):
                zero_branches.append(branch)
        current_branch = (zero_branches[0], zero_branches[1])[zero_branches[0].nodeA < zero_branches[1].nodeB]
        current_node = current_branch.nodeB
        while current_node != 0:
            path += "-"
            path += "[" + str(matrix[current_branch.nodeA][current_branch.nodeB]) + "]-"
            path += str(current_node)
            for branch in true_branches:
                if branch.is_incident_to(current_node) and branch != current_branch:
                    current_node = (branch.nodeA, branch.nodeB)[branch.nodeA == current_node]
                    current_branch = branch
                    break
        path += '-[' + str(matrix[current_branch.nodeA][current_branch.nodeB]) + ']-0'
        print("Solution Path:", path)

    def update_solution_with_missing_branches_if_needed(self, added_branch):
        did_change = True
        did_exclude = False
        new_branch = added_branch
        while did_change is True or new_branch is not None or did_exclude is True:
            did_change = exclude_branches_for_filled_nodes(self)
            if new_branch is not None:
                did_exclude = exclude_possible_short_circuit_after_adding_branch(self, new_branch)
            else:
                did_exclude = False
            # if did_exclude is True or did_change is True:
            new_branch = include_branches_if_needed(self)
            if new_branch == Branch(-1, -1):
                self.impossible = True
                return
            # else:
            #     new_branch = None



def exclude_branches_for_filled_nodes(solution) -> bool:
    did_change = False
    for i in range(matrix_size):
        if solution.has_two_adjacents_to_node(i):
            for j in range(matrix_size):
                if i == j:
                    continue
                branch_to_exclude = Branch(i, j)
                if branch_to_exclude not in solution.branches.keys():
                    solution.branches[branch_to_exclude] = False
                    did_change = True
    return did_change



def include_branches_if_needed(solution) -> Optional[Branch]:
    for i in range(matrix_size):
        number_of_excluded_branches = 0
        for b in solution.branches.keys():
            if b.is_incident_to(i) and solution.branches[b] is False:
                number_of_excluded_branches += 1
        if number_of_excluded_branches > matrix_size - 3:
            # print("Error in number of excluded branches on node: ", i)
            # print('Impossible solution')
            return Branch(-1, -1)
        if number_of_excluded_branches == matrix_size - 3:
            for j in range(matrix_size):
                if i == j:
                    continue
                current_branch = Branch(i, j)
                if current_branch not in solution.branches.keys():
                    # print('ibin: adding Branch: ', current_branch)
                    solution.branches[current_branch] = True
                    return current_branch
                    # if solution.has_two_adjacents_to_node(i):
                    # exclude_possible_short_circuit_after_adding_branch(solution, current_branch)
    return None


def exclude_possible_short_circuit_after_adding_branch(solution, branch: Branch) -> bool:
    did_exclude = False
    if solution.number_of_included_branches() == matrix_size - 1:
        return did_exclude
    j = branch.nodeA
    m = branch.nodeB
    if solution.has_two_adjacents_to_node(m):
        for i in range(matrix_size):
            if i == j:
                continue
            branch_to_exclude = Branch(i, j)
            if branch_to_exclude in solution.branches.keys():
                continue
            if has_included_adjacents(solution, branch_to_exclude):
                solution.branches[branch_to_exclude] = False
                did_exclude = True
    if solution.has_two_adjacents_to_node(j):
        for k in range(matrix_size):
            if k == m:
                continue
            branch_to_exclude = Branch(k, m)
            if branch_to_exclude in solution.branches.keys():
                continue
            if has_included_adjacents(solution, branch_to_exclude):
                solution.branches[branch_to_exclude] = False
                did_exclude = True
    return did_exclude


def has_included_adjacents(solution, branch) -> bool:
    node_a_included = False
    node_b_included = False
    included_branches = []
    for b in solution.branches.keys():
        if solution.branches[b] is True:
            included_branches.append(b)
    for b in included_branches:
        if b.is_incident_to(branch.nodeA):
            node_a_included = True
            continue
        if b.is_incident_to(branch.nodeB):
            node_b_included = True
    return node_a_included and node_b_included


def are_incident(branch1: Branch, branch2: Branch) -> bool:
    return branch1.nodeA == branch2.nodeA or branch1.nodeA == branch2.nodeB or\
           branch1.nodeB == branch2.nodeA or branch1.nodeB == branch2.nodeB


def mt_func(queue, p_counter, best_solution_record):
    # while queue.get() and p_counter != 0:
    print(os.getpid(), "working")
    while True:
        # time.sleep(0.1)
        try:
            solution = queue.get(block=True, timeout=0.001)
        except:
            print('Queue is empty')
            break
       # print('Flag before: ',p_counter.value)
        with p_counter.get_lock():
            p_counter.value += 1
        make_branches(solution, p_counter, queue, best_solution_record)
        with p_counter.get_lock():
            p_counter.value -= 1
        #print('Flag after: ', p_counter.value)

if __name__ == '__main__':
    initial_solution = Solution()
    solutions_queue.enqueue(initial_solution)
    counter = 0
    start = time.time()

    m = multiprocessing.Manager()
    sharedQueue = m.Queue()

    p_counter = Value('i', 0)
    best_solution_record = Value('f', float('inf'))

    sharedQueue.put(initial_solution)

    # pool = multiprocessing.Pool(4, mt_func, (sharedQueue, p_counter, best_solution_record))

    print("before")

    # sharedQueue.join()

    print('after')

    processes = {}

    num_processes = 5

    for n in range(num_processes):
        processes[n] = Process(target=mt_func, args=(sharedQueue, p_counter, best_solution_record))
        processes[n].start()

    for k in range(num_processes):
        processes[k].join()


    # p1 = multiprocessing.Process(target=mt_func, args=(sharedQueue, p_counter, best_solution_record))
    # p2 = multiprocessing.Process(target=mt_func, args=(sharedQueue, p_counter, best_solution_record))
    # p3 = multiprocessing.Process(target=mt_func, args=(sharedQueue, p_counter, best_solution_record))
    # p4 = multiprocessing.Process(target=mt_func, args=(sharedQueue, p_counter, best_solution_record))
    # #
    # p1.start()
    # p2.start()
    # p3.start()
    # p4.start()

    # p1.join()
    # p2.join()
    # p3.join()
    # p4.join()

    # time.sleep(15)
    #
    def print_results():
        print('Algorithm finished\n')
        print('Best solution is: ', best_solution_record.value)
        # best_solution.print_solution()
    #
    print_results()
    end = time.time()
    time_delta = end - start
    if time_delta < 1:
        time_delta = round(time_delta, 6)
    else:
        time_delta = round(time_delta, 3)
    print('\nTime elapsed:', time_delta)
