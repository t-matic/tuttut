import numpy as np
import pretty_midi
from pretty_midi.utilities import note_name_to_number
import theory
import math
import networkx as nx
import matplotlib.pyplot as plt

def note_number_to_note(note_number):
  note = str(pretty_midi.note_number_to_name(note_number))
  (degree, octave) = (note[:-1], note[-1:]) if not '-' in note else (note[:-2], note[-2:])
  degree = theory.Degree(degree)
  
  return theory.Note(degree, octave)

def midi_note_to_note(note):
  return note_number_to_note(note.pitch)

def measure_length_ticks(midi, time_signature):
  measure_length = midi.time_to_tick(midi.get_beats()[time_signature.denominator])
  return measure_length

def get_notes_between(midi, notes, begin, end):
  res = []
  for note in notes:
    start = midi.time_to_tick(note.start)
    if start >= begin and start< end:
      res.append(note)

  return res
  
def note_to_fret(string, note):
  string_name = string.degree.value + str(string.octave)
  note_name = note.degree.value + str(note.octave)
  n_string = pretty_midi.note_name_to_number(string_name)
  n_note = pretty_midi.note_name_to_number(note_name)

  return n_note - n_string

def get_non_drum(instruments):
  res = []
  for instrument in instruments:
    if not instrument.is_drum:
      res.append(instrument)
  return res

def get_all_possible_notes(tuning, nfrets = 20):
  nstrings = len(tuning.strings)
  res = []
  for string in tuning.strings:
    string_note_number = note_name_to_number(string.degree.value + str(string.octave))
    string_notes = []
    for ifret in range(nfrets):
      string_notes.append(note_number_to_note(string_note_number+ifret))
    res.append(string_notes)
  
  return res

def distance_between(x, y):
  return math.dist(x,y)

def get_notes_in_graph(G, note):
  nodes = list(G.nodes)
  res = []
  for node in nodes:
    if node == note:
      res.append(node)
  return res

def build_path_graph(G, note_arrays):
  res = nx.DiGraph()

  for x, note_array in enumerate(note_arrays):
    for y, possible_note in enumerate(note_array):
      res.add_node(possible_note, pos = (x, y))

  for idx, note_array in enumerate(note_arrays[:-1]): #Check every array except the last
    for possible_note in note_array:
      for possible_target_note in note_arrays[idx+1]:
        if (G.nodes[possible_note]["pos"][0] != G.nodes[possible_target_note]["pos"][0]):
          res.add_edge(possible_note, possible_target_note, distance = G[possible_note][possible_target_note]["distance"])

  return res 

def find_shortest_path(path_graph, note_arrays):
  #shortest_path = [note_array[0] for note_array in note_arrays]
  shortest_path = None

  for possible_source_node in note_arrays[0]:
    for possible_target_node in note_arrays[-1]: 
      try:
        #print("Source : ", path_graph.nodes[possible_source_node]["pos"])
        #print("Target : ", path_graph.nodes[possible_target_node]["pos"])
        path = nx.shortest_path(path_graph, possible_source_node, possible_target_node, weight = "distance")
        path_length = get_path_length(path_graph, path)
        if not shortest_path or path_length < get_path_length(path_graph, shortest_path):
          shortest_path = path
      except nx.NetworkXNoPath:
        print("No path ???")
        display_path_graph(path_graph)

  print("Shortest path :", shortest_path)
  return shortest_path

def find_paths(path_graph, note_arrays):
  paths = []
  for possible_source_node in note_arrays[0]:
    for possible_target_node in note_arrays[-1]: 
      try:
        path = nx.shortest_path(path_graph, possible_source_node, possible_target_node, weight = "distance")
        path_length = get_path_length(path_graph, path)
        paths.append(path)
      except nx.NetworkXNoPath:
        print("No path ???")
        display_path_graph(path_graph)

  return paths

def find_shortest_closest_path(G, paths, previous_notes):

  shortest_closest = paths[0]

  for path in paths:
    if is_better_distance_length(G, shortest_closest, path, previous_notes):
      shortest_closest = path

  return shortest_closest

def euclidean_distance(p1, p2):
  return np.linalg.norm(np.array(p1) - np.array(p2))

def get_centroid(G, path):
  vectors = [G.nodes[note]["pos"] for note in path]
  x = [v[0] for v in vectors]
  y = [v[1] for v in vectors]
  centroid = (sum(x) / len(vectors), sum(y) / len(vectors))
  return centroid

def is_better_distance_length(G, shortest_closest, path, previous_notes):
  centroid = get_centroid(G, path)
  
  if len(previous_notes) > 0:
    previous_centroid = get_centroid(G, previous_notes)
  else: 
    previous_centroid = (0,0)

  shortest_closest_centroid = get_centroid(G, shortest_closest)
  length = get_path_length(G, path)
  shortest_closest_length = get_path_length(G, shortest_closest)

  distance = euclidean_distance(centroid, previous_centroid)
  shortest_closest_distance = euclidean_distance(shortest_closest_centroid, previous_centroid)

  length_weight = 1
  distance_weight = 0

  return length * length_weight + distance * distance_weight < shortest_closest_length * length_weight + shortest_closest_distance * distance_weight

def get_path_length(G, path):
  res = 0
  for i in range(len(path)-1):
    res += G[path[i]][path[i+1]]["distance"]
  return res
  
def display_path_graph(path_graph):
  edge_labels = nx.get_edge_attributes(path_graph,'distance')
  pos=nx.get_node_attributes(path_graph,'pos')
  nx.draw(path_graph, pos, with_labels=True)
  nx.draw_networkx_edge_labels(path_graph, pos, edge_labels = edge_labels)
  plt.show()

def fill_measure_str(str_array):
  maxlen = len(max(str_array, key = len))
  res = []
  for str in str_array:
    res.append(str.ljust(maxlen, "-"))
  return res

if __name__ == "__main__":
  arrays = [[1,11,111,1111], [2,22,222], [3,33]]
  print(arrays[-1])
  G = nx.DiGraph()
  G.add_node(1, pos=(0,0))
  G.add_node(11, pos=(0,1))
  G.add_node(111, pos=(0,2))
  G.add_node(1111, pos=(0,3))
  G.add_node(2, pos=(1,0))
  G.add_node(22, pos=(1,1))
  G.add_node(222, pos=(1,2))
  G.add_node(3, pos=(2,0))
  G.add_node(33, pos=(2,1))

  G.add_edge(1, 2, distance = 1)
  G.add_edge(11, 2, distance = 2)
  G.add_edge(111, 2, distance = 1)
  G.add_edge(1111, 2, distance = 1)
  G.add_edge(1, 22, distance = 1)
  G.add_edge(11, 22, distance = 2)
  G.add_edge(111, 22, distance = 1)
  G.add_edge(1111, 22, distance = 1)
  G.add_edge(1, 222, distance = 1)
  G.add_edge(11, 222, distance = 2)
  G.add_edge(111, 222, distance = 1)
  G.add_edge(1111, 222, distance = 1)


  G.add_edge(2, 3, distance = 1)
  G.add_edge(22, 3, distance = 2)
  G.add_edge(222, 3, distance = 2)
  G.add_edge(2, 33, distance = 1)
  G.add_edge(22, 33, distance = 2)
  G.add_edge(222, 33, distance = 2)
  

  find_shortest_path(G, arrays)

  pos = nx.get_node_attributes(G,'pos')
  nx.draw(G, pos = pos, with_labels = True)
  nx.draw_networkx_edge_labels(G, pos = pos, edge_labels=nx.get_edge_attributes(G,'distance'))
  plt.show()

  
  
  
  
