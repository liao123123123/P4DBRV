# -*- coding: utf-8 -*-
import json
import os
import sys
import math
import pickle
import pydotplus
import networkx as nx
from collections import deque
import matplotlib.pyplot as plt
import pickle


global edge_to_del
edge_to_del = []
#得到节点信息，键为节点，值为label信息
def get_nodes(path, cnt_blk):
    """This method takes .dot file path and returns a dictionary having Node Name and Node Label."""
    """Extracting node information."""
    node_name_label = {}
    # path是第0个参数
    dot_graph = pydotplus.graphviz.graph_from_dot_file(path)
    subgraphs = dot_graph.get_subgraphs()
    for subG in subgraphs:
        for n in subG.get_node_list():
            # 获取属性值label，如下面所示的A、B、C
            # digraph example {
            # A [label="Node A"];
            # B [label="Node B"];
            # C [label="Node C"];
            # A -> B;
            # B -> C;}

            name = n.obj_dict["attributes"].get('label')
            if name and name not in ['__START__', '__EXIT__', ""]:
                # label中有"和,和（）都删掉
                if ';' in name:
                    name = name.replace(';', '')
                if '"' in name:
                    name = name.replace('"', '')
                if "()" in name and "." not in name:
                    name = name.replace("()", '')
                    # ingress.node A
                    name = cnt_blk + '.' + name
                # 如果name不在node_name_label中，就加入进去
                if name not in node_name_label.values():
                    node_name_label[n.get_name()] = name
                else:
                    cnt = 1
                    key = list(node_name_label.keys())
                    values = list(node_name_label.values())
                    ind = key[values.index(name)]
                    while True:
                        if name + "##" + str(cnt) in node_name_label:
                            cnt += 1
                        else:
                            name = name + "##" + str(cnt)
                            break
                    node_name_label[n.get_name()] = name
    to_del = 'graph'
    del node_name_label[to_del]
    return node_name_label

def get_edges(path, nodes):
	"""This method takes .dot file path and returns a dictionary having Edge Source Node Name and
		Edge details like destination node name, edge label. Extracting edge information."""
	edge_src_details = {}
	edge_src_names = {}
	edges = []
	dot_graph = pydotplus.graphviz.graph_from_dot_file(path)
	count = 0
	for subGraph in dot_graph.get_subgraphs():
		for e in subGraph.get_edge_list():
			edge_src_details[count] = {"src":e.get_source(),"dst":e.get_destination(), "label":e.obj_dict["attributes"]['label']}
			edge_src_names[count] = {"src":e.get_source(),"dst":e.get_destination(), "label":e.obj_dict["attributes"]['label']}
			count+=1

	for e in edge_src_details.keys():
		# print("\n\tEdges : ",edge_src_details[e]['src'],nodes[edge_src_details[e]['src']], edge_src_details[e]['dst'], nodes[edge_src_details[e]['dst']])
		if(edge_src_details[e]['src'] in nodes.keys() and edge_src_details[e]['dst'] in nodes.keys()):
			edges.append({'src':nodes[edge_src_details[e]['src']], 'dst':nodes[edge_src_details[e]['dst']], 'label': edge_src_details[e]['label'].replace('"','')})
	# edges = edges[1:len(edges)-2]
	return edges

def extract_conditionals(filename):
	"""This function creates dictionary of conditionals with its
	corresponding next actions based on the condition
	evaluation " or False"."""
	data = None
	#data用来读.json文件
	with open(filename, 'r') as f:
		data = json.load(f)

	#If any duplicate Conditions present then append "##1", "##2" etc. at the end of the conditionals.
	node_to_condition = {}
	#pipelines-conditionals-source_info-source_fragment
	for name in data['pipelines']:
		for condition in name['conditionals']:
			if 'source_info' in condition.keys():
				if str(condition['source_info']['source_fragment']) not in node_to_condition.values():
					node_to_condition[str(condition['name'])] = str(condition['source_info']['source_fragment'])
				else:
					cnt = 1
					key = node_to_condition.keys()
					values = node_to_condition.values()
					# ind = key[values.index(str(condition['source_info']['source_fragment']))]
					while(1):
						if str(condition['source_info']['source_fragment'])+"##"+str(cnt) in node_to_condition:
							cnt += 1
						else:
							node_to_condition[str(condition['name'])] = str(condition['source_info']['source_fragment']) + "##" + str(cnt)
							break

			else:
				if str(condition['true_next']) != 'None' and str(condition['true_next']) not in node_to_condition.values():
					node_to_condition[str(condition['name'])] = str(condition['true_next'])
				else:
					cnt = 1
					key = node_to_condition.keys()
					values = node_to_condition.values()
					# ind = key[values.index(name)]
					while(1):
						if str(condition['true_next'])+"##"+str(cnt) in node_to_condition.values():
							cnt += 1
						else:
							node_to_condition[str(condition['name'])] = str(condition['true_next']) + "##" + str(cnt)
							break
				if str(condition['false_next']) != 'None' and str(condition['false_next']) not in node_to_condition.values():
					node_to_condition[str(condition['name'])] = str(condition['false_next'])
				else:
					cnt = 1
					key = node_to_condition.keys()
					values = node_to_condition.values()
					# ind = key[values.index(name)]
					while(1):
						if str(condition['false_next'])+"##"+str(cnt) in node_to_condition.values():
							cnt += 1
						else:
							node_to_condition[str(condition['name'])] = str(condition['false_next']) + "##" + str(cnt)
							break

	conditions_to_nextstep = {}
	for name in data['pipelines']:
		for condition in name['conditionals']:
			if 'source_info' in condition.keys() and str(condition['source_info']['source_fragment']) not in conditions_to_nextstep.keys():
				conditions_to_nextstep[str(condition['source_info']['source_fragment'])] = {'true_next':str(condition['true_next']),
																				'false_next':str(condition['false_next'])}
			elif 'source_info' in condition.keys() and str(condition['source_info']['source_fragment']) in conditions_to_nextstep.keys():
				cnt = 1
				while(1):
					if str(condition['source_info']['source_fragment'])+"##"+str(cnt) in conditions_to_nextstep.keys():
						cnt += 1
					else:
						conditions_to_nextstep[str(condition['source_info']['source_fragment'])+ "##" + str(cnt)] = {'true_next':str(condition['true_next']),
																				'false_next':str(condition['false_next'])}
						break

	to_delete = []
	for node in node_to_condition:
		if node_to_condition[node] in node_to_condition.keys():
			to_delete.append(node)

	if len(to_delete) > 0:
		for n in to_delete:
			del node_to_condition[n]
	return conditions_to_nextstep, node_to_condition

def extract_actions(filename, cnt_blk):
	global CONTROL
	CONTROL = cnt_blk
	data = None
	action_list = []
	with open(filename, 'r') as f:
		data = json.load(f)

	for action in data['actions']:
		if cnt_blk in str(action):
			action_list.append(str(action['name']))

	action_list = list(set(action_list))
	return action_list

def extract_tables_actions(filename, cnt_blk, actions):
	data = None
	name_to_action = {}
	tbl_to_action = {}
	tbl_to_table = {}
	with open(filename, 'r') as f:
		data = json.load(f)

	for name in data['pipelines']:
		for table in name["tables"]:
			if cnt_blk in table["name"]:
				name_to_action[str(table["name"]) if(cnt_blk in table["name"]) else table["name"]] =  [str(x) for x in table["actions"]]
			else:
				#表格到动作
				tbl_to_action[str(table["name"])] =  [str(x) for x in table["actions"]]
				#表格到表格
				tbl_to_table[str(table["name"])] = [str(x) for x in table["next_tables"].values()]
				# print "\n\t TBL_TO_ACTION : ",str(table["name"]),table["actions"]
				# print "\n\t TBL_TO_nexttables : ",str(table["name"]),[str(x) for x in table["next_tables"].values()]
	return name_to_action, tbl_to_action, tbl_to_table

def eliminate_edge(edge, edges, nodes):
	if edge['dst'] in nodes:
		return edge['dst']
	else:
		for e in edges:
			if(e['src'] == edge['dst']):
				nxt_node = eliminate_edge(e, edges, nodes)
				edge_to_del.append(e)
				break
			else:
				nxt_node = -1
		return nxt_node

def append_missing_edges(table_action, edges, leaf_nodes):
	new_edges = []
	ed_to_del = []
	for e in edges:
		if e['src'] in table_actions.keys():
			ed_to_del.append(e)
			for ac in table_actions[e['src']]:
				new_edges.append({'src':e['src'], 'dst':ac, 'label':''})
				new_edges.append({'src':ac, 'dst':e['dst'], 'label':''})
		elif e['dst'] in leaf_nodes and e['dst'] in table_actions.keys():
			for ac_1 in table_actions[e['dst']]:
				new_edges.append({'src':e['dst'], 'dst':ac_1, 'label':''})

	edges = edges + new_edges
	for de in ed_to_del:
		if de in edges:
			edges.remove(de)
	return edges

#This method extracts the instance name of metadata variable.
def get_meta_inst_name(p4_code, cnt_blk, meta):
	meta_inst = ""
	meta_ind_beg = p4_code.find(" ",p4_code.find(meta, p4_code.find("control "+str(cnt_blk))))
	meta_ind_end = p4_code.find(',',meta_ind_beg)

	print ("\n\n@#@##@: ",p4_code[meta_ind_beg: meta_ind_end])

	meta_inst = p4_code[meta_ind_beg: meta_ind_end]
	meta_inst = meta_inst.strip()
	return meta_inst

# This method extract all the paths and saves the all paths in text file and save pickle file for further use.
#def extract_paths(G, file_path):
	##start_node = [v for v, d in G.in_degree() if d == 0]
	# print "\n\t LEAF NODES: ", leaf_nodes
	# print "\n\t START NODE : ",start_node

	##for leaf in leaf_nodes:
	   # for path in nx.all_simple_paths(G, source=start_node[0], target=leaf ):
	        #path_list.append(path)
	        #print "\n\t path: ",path

	# Extract edges in the path.
	#path_list_edges = []
	#for path in map(nx.utils.pairwise, path_list):
	    #path_list_edges.append(list(path))

	#path_list_edges_weights = []
	#for path in path_list_edges:
	    #weighted_path = list()
	    #weight_sum = 0
	    #for edge in path:
	        # find the edge in weighted_edges and update the edge including weight in "path_list_edges_weights"
	        #matched_edge = list(filter(lambda e: e['src'] == edge[0] and e['dst'] == edge[1], weighted_edges))
	        #weight_sum = weight_sum + int(matched_edge[0]['weight'])
	    #path_list_edges_weights.append([path,weight_sum])

	# Creating paths by merging the edges.[[(A,B),(C,D)],10] to [[A,B,C,D],10]
	#all_paths = []
	#for path in path_list_edges_weights:
		#l = []
		#for e in path[0]:
			#l.append(str(e[0]))
		#l.append(str(e[1]))
		#all_paths.append([l,path[1]])

	#with open(file_path+"path_list.pkl",'wb') as f:
	    #pickle.dump(path_list_edges_weights, f, protocol=2)

	#new_file=open(file_path+'all_paths.txt','w')
	#data = ""
	#for p in all_paths:
		#data = data + ' --> '.join(p[0]) + ' ## '+str(p[1])+"\n\n"
		#print("\n\tPATHS: ",p)

	#new_file.write(data)
	#new_file.close()

def create_cfg(edges):

	edges_tuples = []

	for e in edges:
		edges_tuples.append((e['src'], e['dst'], 0))
	#去除重复的元素 ，set中没有重复元素。
	edges_tuples = list(set(edges_tuples))
	for i in edges_tuples:
		print (i)


	G = nx.DiGraph()
	G.add_weighted_edges_from(edges_tuples)

	nx.draw_shell(G, with_labels = True, arrows=True, font_size=5, node_size=80, node_color='orange')
	plt.savefig(file_path+'graph.pdf', dpi = 300, format='pdf', bbox_inches="tight")
	plt.show(block=False)
	try:
		cycle =nx.algorithms.cycles.find_cycle(G, orientation="original")
	except:
		cycle=0
	while cycle :
		try:
			G.remove_edge(cycle[-1][0],cycle[-1][1])
		except:
			pass
		try:
			cycle =nx.algorithms.cycles.find_cycle(G, orientation="original")
		except:
			cycle=0


	#####################################################################
	################## CYCLE DETECTION & ELIMINATION ####################
	#####################################################################

	# cycle = []
	# topological_order = []
	# rev_topological_order = []
	# while(1):
	# 	G = nx.DiGraph()
	# 	# G.add_nodes_from(all_clean_nodes)
	# 	G.add_weighted_edges_from(edges_tuples)

	# 	try:
	# 		cycle=nx.algorithms.cycles.find_cycle(G, orientation="original")
	# 		rev_topological_order = list(reversed(list(nx.topological_sort(G))))
	# 	except:
	# 		print("\n\t Cycle found in the graph...!!!", cycle)
	# 	cycle1=[]
	# 	cycle2=cycle
	# 	for i in cycle:
	# 		for j in cycle2:
	# 			if (i[0] == j[1]):
	# 				temp_edge=(j[0],j[1],0)
	# 				cycle1.append(temp_edge)
	# 		print 'cycle1:',cycle1

	# 		print "\n\tCYCLE: ",cycle1[-1]
	# 		edges_tuples.remove(cycle1[-1])
	# 		print "\n\tUpdate Edges after Removing Cycles: ",len(edges_tuples), edges_tuples
	#####################################################################
	################## CYCLE DETECTION & ELIMINATION ####################
	#####################################################################
	#G = nx.DiGraph()
	#G.add_weighted_edges_from(edges_tuples)

	# cycle=nx.algorithms.cycles.find_cycle(G, orientation="original")
	# print "\n\t >>>>>>>>>><<<<<<<<<<< CYCLES : ",cycle
	# to_rem = (cycle[0][0], cycle[0][1], 0)
	# print "\n\t >>>>>>>>>><<<<<<<<<<< to_rem : ",to_rem, to_rem in edges_tuples
	# edges_tuples.remove(to_rem)

	# print "UPDATED EDGES TUPLES: >>>>>>>>>>>>>"
	# for i in edges_tuples:
	# 	print i
	# G = nx.DiGraph()
	# G.add_weighted_edges_from(edges_tuples)
	# cycle=nx.algorithms.cycles.find_cycle(G, orientation="original")
	# print "\n\t >>>>>>>>>><<<<<<<<<<< CYCLES : ",cycle
	topological_order = list(nx.topological_sort(G))
	rev_topological_order = list(reversed(list(nx.topological_sort(G))))

	#取出叶节点
	leaf_vertex = [v for v, d in G.out_degree() if d == 0]

	####################################
	#### START BALL-LARUS ALGORITHM ####
	####################################
	weighted_edges = []
	for e in edges_tuples:
		weighted_edges.append({'src':e[0], 'dst':e[1], 'weight':e[2]})

	num_path = {}
	for v in rev_topological_order:
		if v in leaf_vertex:
			#num_path是从v点到exit的数目
			num_path[v] = 1
		else:
			num_path[v] = 0
			#e是v的出边
			for e in G.out_edges(v):
				#找到对应边是第几个索引
				ind = weighted_edges.index({'src':e[0], 'dst':e[1],'weight': 0})
				weighted_edges[ind]['weight'] = num_path[v]
				num_path[v] = num_path[v] + num_path[e[1]]
	e_list2 =[]
	for i in weighted_edges:
		e_list1 = [(i["src"], i["dst"], i["weight"])]
		#print(e_list1)
		e_list2.append(e_list1)
	#print(e_list2)
	#e_list2 = [['A', 'B', 0.5], ['B', 'C', 0.8], ['C', 'D', 0.3]]
	#
	#flat_list = [item for sublist in e_list2 for item in sublist]
	#
	#print(flat_list)  # 输出: ['A', 'B', 0.5, 'B', 'C', 0.8, 'C', 'D', 0.3]
	flat_list = [item for sublist in e_list2 for item in sublist]
	print(flat_list)
	G1 = nx.DiGraph()
	G1.add_weighted_edges_from(flat_list)
	nx.draw(G1, with_labels=True)
	pos=nx.spring_layout(G1)
	labels = nx.get_edge_attributes(G1,'weight')
	nx.draw_networkx_edge_labels(G1,pos,edge_labels=labels)


	###################################
	#### END BALL-LARUS ALGORITHM ######
	####################################

	return G1, weighted_edges

def get_next_same_con(new_data,node,req_ind):
	#This function identifies the index of next similar condition in the code.
	cnt = int(node.split("##")[1])
	search_string = node.split("##")[0]
	req_ind = 0
	for i in range(cnt+1):
		req_ind = new_data.find(search_string, req_ind+len(search_string))
		# print "\n\t>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<",req_ind, new_data[req_ind:req_ind+100]
	return req_ind

def augmenter(p4_filename, jsonfile, dotfile, cnt_blk, meta, weighted_edges, file_path):
	import re

	# jsonfile = "./dot files/03-L2_Flooding/Other ports/l2_flooding_other_ports.json"
	# jsonfile = "./dot files/09-Traceroutable/traceroutable.json"
	file_name = os.path.split(p4_filename)[1]
	#file_path = os.path.split(p4_filename)[0]

	# if file_path != "":
	# 	file_path = file_path+'/'
	# 	print "\n\tPATH : ",'/'+file_path
	# else:
	# 	file_path = ""
	# 	print "\n\tPATH : ",os.getcwd()+'/'+file_path

	conditions, node_to_condition = extract_conditionals(jsonfile)
	actions = extract_actions(jsonfile, cnt_blk)
	table_actions, tbl_to_action, tbl_to_table = extract_tables_actions(jsonfile, cnt_blk, actions)
	tables = table_actions

	# for ta in table_actions.keys():
	# 	for ac in table_actions[ta]:
	# 		if ac not in actions:
	# 			actions.append(ac)

	# conditions, node_to_condition = extract_conditionals(jsonfile)
	# nodes = actions + table_actions.keys() + conditions.keys()
	# additional_edges = create_additional_edges(nodes, node_to_condition, conditions, tbl_to_action, tbl_to_table)
	# all_nodes = get_nodes(dotfile, nodes)
	# edges = get_edges(dotfile, all_nodes, tbl_to_action)
	# all_edges = create_all_edges(edges, table_actions) + additional_edges

	# graph,weighted_edges = create_cfg(nodes, all_edges, table_actions.keys(), actions)
	# tables = table_actions

	print ("\n\tTables :")
	print (tables.keys())


	print ("\n\t@@Weighted Edges :")
	print (weighted_edges)

	data = None
	with open(p4_filename, 'r') as f:
		data = f.read()
		meta_inst = get_meta_inst_name(data, cnt_blk, meta)
		meta_inst = meta_inst + '.BL'
		new_data = data
		nodes_and_weights = {}

		if len(weighted_edges) > 0:
			bits = int(math.ceil(math.log(len(weighted_edges), 2)) + (8 - (math.ceil(math.log(len(weighted_edges), 2)) % 8)))
		else:
			bits = 0

		index_metadata = new_data.find('{', new_data.find('struct '+meta)) + 1
		meta_data = "\n\tbit<"+str(bits)+"> BL; \n"
		if index_metadata != -1:
			new_data = new_data[0:index_metadata] + meta_data + new_data[index_metadata+1:]
		else:
			print ("\n\t Declaration of <"+meta+"> is not present in this file.")
			exit(0)

		for we in weighted_edges:
			src = we['src']
			dst = we['dst']

			weight = int(we['weight'])

			#If the "src" Node is an action then annotate the BL valriable to the Action.
			if src in actions:
				print("\n\t ####1) ",we)
				# if 'NoAction' in src:
				#     continue
				nodes_and_weights[src] = weight
				if len(src.split('.')) > 1:
					src = src.split('.')[1]
					search_string = "action "+ str(src)
				else:
					search_string = "action "+ str(src)

				annotate_string = "\n\t "+meta_inst+" = "+meta_inst+" + "+str(weight)+";\n"

				if new_data.find(search_string) != -1 and int(weight) > 0:
					req_ind = new_data.find('{', new_data.find(search_string)) + 1
					if req_ind != -1:
						new_data = new_data[0:req_ind] + annotate_string + new_data[req_ind+1:]
				# print("\n\tindex: ",req_ind," : ", src)
			#If the "dst" Node is an action then annotate the BL valriable to the Action.
			elif dst in actions:
				print("\n\t ####2) ",we)
				# if 'NoAction' in dst:
				#     continue
				nodes_and_weights[dst] = weight
				if len(dst.split('.')) > 1:
					dst = dst.split('.')[1]
					search_string = "action "+ str(dst)
				else:
					search_string = "action "+ str(dst)
				annotate_string = "\n\t\t "+meta_inst+" = "+meta_inst+" + "+str(weight)+";\n"
				if new_data.find(search_string) != -1 and int(weight) > 0:
					req_ind = new_data.find('{', new_data.find(search_string)) + 1
					if req_ind != -1:
						new_data = new_data[0:req_ind] + annotate_string + new_data[req_ind+1:]
			elif src in conditions.keys() and dst in tables.keys():
				print("\n\t ####3) ",we)
				search_string = dst.split('.')[1]
				nodes_and_weights[src] = weight
				annotate_string = "\n\t"+meta_inst+" = "+meta_inst+" + "+str(weight)+";\n"
				req_ind = new_data.find(cnt_blk)
				req_ind = new_data.find("apply",req_ind)
				req_ind = new_data.find(search_string+".apply()", req_ind)
				req_ind = new_data.find(";",req_ind)
				print("\n\t req_ind: ",req_ind, new_data[req_ind:req_ind+20])
				# req_ind = new_data.find("}", req_ind)

				# print "\n\tHEREEEEEEE : ",src ,req_ind
				if int(weight) > 0 and req_ind != -1:
						new_data = new_data[0:req_ind+1] + annotate_string + new_data[req_ind+1:]

			elif src in tables.keys() and dst in conditions.keys():
				print("\n\t ####4) ",we)
				nodes_and_weights[src] = weight
				annotate_string = "\n\t"+meta_inst+" = "+meta_inst+" + "+str(weight)+";\n"
				if '##' not in dst:
					search_string = dst
					req_ind = new_data.find(cnt_blk)
					req_ind = new_data.find(search_string, req_ind)
					# req_ind = new_data.rfind("{",0,req_ind)
					print("\n\t >>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<req_ind: ",new_data[req_ind-10:req_ind])
					# req_ind = new_data.find("}", req_ind)
				elif '##' in dst:
					cnt = int(dst.split('##')[1])
					search_string = dst.split('##')[0]
					req_ind = new_data.find(cnt_blk)
					req_ind = get_next_same_con(new_data,dst,req_ind)
					print("\n\t >>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<req_ind: ",new_data[req_ind-10:req_ind])
					# for i in range(cnt):
					# 	req_ind = new_data.find(search_string, req_ind+len(search_string))
					# req_ind = new_data.find("{",0,req_ind)

				if int(weight) > 0 and req_ind != -1:
					new_data = new_data[0:req_ind+1] + annotate_string + new_data[req_ind+1:]
			elif src in conditions.keys() and dst in conditions.keys():
				print("\n\t ####5) ",we)
				src_con_ind = 0
				dst_con_ind = 0
				search_string = dst
				nodes_and_weights[src] = weight
				annotate_string = "\n\t\t "+meta_inst+" = "+meta_inst+" + "+str(weight)+";\n"
				req_ind = new_data.find(cnt_blk)
				req_ind = new_data.find("apply")

				if "##" not in src:
					src_con_ind = new_data.find(src, req_ind)
				else:
					search = src.split("##")[0]
					src_con_ind = get_next_same_con(new_data,src,req_ind)


				if "##" not in dst:
					dst_con_ind = new_data.find(dst, req_ind)
				else:
					dst_con_ind = get_next_same_con(new_data,dst,req_ind)

				# print("\n\t >>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<SRC req_ind: ",new_data[src_con_ind-10:src_con_ind])
				# print("\n\t >>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<DST req_ind: ",new_data[dst_con_ind-10:dst_con_ind])

				if "elif" not in new_data[src_con_ind-10:src_con_ind] and "if" in new_data[src_con_ind-10:src_con_ind]:
					if "elif" not in new_data[dst_con_ind-10:dst_con_ind] and "if" in new_data[dst_con_ind-10:dst_con_ind]:
						#If src and dst are IF conditions then augment in between them.
						req_ind = new_data.find("{",src_con_ind)

				if "elif" in new_data[src_con_ind-10:src_con_ind]:
					if "elif" in new_data[dst_con_ind-10:dst_con_ind]:
						#If src and dst are ELIF conditions then augment inside both of them.
						req_ind = new_data.find("{",dst_con_ind)

				if "elif" in new_data[src_con_ind-10:src_con_ind]:
					if "elif" not in new_data[dst_con_ind-10:dst_con_ind] and "if" in new_data[dst_con_ind-10:dst_con_ind]:
						#If src is ELIF and dst is IF conditions then augment in between them.
						req_ind = new_data.find("{",src_con_ind)

				if "elif" not in new_data[src_con_ind-10:src_con_ind] and "if" in new_data[src_con_ind-10:src_con_ind]:
					if "elif" in new_data[dst_con_ind-10:dst_con_ind]:
						#If src is ELIF and dst is IF conditions then augment in between them.
						req_ind = new_data.find("{",dst_con_ind)
				# req_ind = new_data.find(search_string, req_ind)
				# req_ind = new_data.find("{",req_ind)
				# req_ind = new_data.rfind("{",0,req_ind)
				# print "@@@@ : ", req_ind, new_data[req_ind : req_ind+20]
				stk = deque()
				ind = 0
				for i in range(req_ind, len(new_data)-1):
				    if new_data[i] == '{':
				        stk.append(new_data[i])
				    elif new_data[i] == '}':
				        stk.pop()
				    if not stk:
				        ind = i
				        break
				req_ind = ind
				if int(weight) > 0 and req_ind != -1:
					new_data = new_data[0:req_ind+1] + annotate_string + new_data[req_ind+1:]

	with open(file_path+file_name.split('.')[0]+"_augmented.p4", 'w') as f:
		f.write(new_data)

	print("i'm ok .")



p4filename = ""
jsonfile = ""
dotfile = ""
cnt_blk = ""
meta = ""



if len(sys.argv) != 6:
	print("\n\t Please provide <p4filename.p4> <dot_file_name.dot> <json_file_name.json> <control block name(eg: \"MyIngress\")> <struct metadata name(eg: \"metadata_t\")>")
	exit(0)
else:
	p4filename = str(sys.argv[1])
	dotfile = str(sys.argv[2])
	jsonfile = str(sys.argv[3])
	cnt_blk = str(sys.argv[4])
	meta = str(sys.argv[5])

file_path = os.path.split(p4filename)[0]
if file_path != "":
	file_path = file_path+'/'
	print ("\n\tPATH : ",'/'+file_path)
else:
	file_path = ""
	print ("\n\tPATH : ",os.getcwd()+'/'+file_path)

#从.dot文件中得到节点
nodes_dict = get_nodes(dotfile, cnt_blk)
nodes = nodes_dict.values()

#从.dot文件中得到边
edges = get_edges(dotfile, nodes_dict)
print ("\n\tEDGES : ",len(edges))
for e in edges:
	print (e)

"""Extracting Conditionals to nextNode and Controller generated to Conditionals from the json file."""
#从.json文件中得到Conditionals譬如!hdr.stag.isValid()

conditions_to_nextstep, node_to_condition = extract_conditionals(jsonfile)
print("\n\t CONDITION TO NEXTSTEP: ", conditions_to_nextstep)
print("\n\t NODE TO CONDITION: ", node_to_condition)

actions = extract_actions(jsonfile, cnt_blk)
print("\n\t ACTIONS:", len(actions), actions)

# table_actions: ingress中的actions
# tbl_to_action: 可能还有egress的actions
# tbl_to_table：表之间的转换
table_actions, tbl_to_action, tbl_to_table = extract_tables_actions(jsonfile, cnt_blk, actions)
print("\n\t TABLES: ", table_actions.keys())
print("\n\t TABLE ACTIONS: ", table_actions)

actual_nodes = []
table_conditions = []
#实际节点= condition + key + actions
actual_nodes = list(conditions_to_nextstep.keys()) + list(table_actions.keys()) + actions
table_conditions = list(conditions_to_nextstep.keys()) + list(table_actions.keys())

print ("\n\tNODES(Before Removing) : ",len(nodes),nodes)
print ("\n\tACTUAL NODES : ",len(actual_nodes), actual_nodes)
print ("\n\tTABLE CONDITIONS: ", len(table_conditions), table_conditions)

to_del = []
for n in nodes:
    if n not in actual_nodes:
        to_del.append(n)

nodes = list(nodes)
for d in to_del:
    nodes.remove(d)

nodes += actions
print ("\n\tNODES(After Removing + actions) : ",len(nodes),nodes)

rel_edge = edges
for e in rel_edge:
	dst = eliminate_edge(e,edges,nodes)
	if dst != -1:
		e['dst'] = dst
	else:
		edge_to_del.append(e)


for e in edge_to_del:
	if e in rel_edge:
		rel_edge.remove(e)

print ("\n\t EDGE TO DELETE : ", len(edge_to_del),edge_to_del)

print ("\n\t EDGES AFTER ELIMINATING: ",len(rel_edge))
for i in rel_edge:
	print(i)

edges_tuples = []
for e in edges:
	edges_tuples.append((e['src'], e['dst'], 0))
edges_tuples = list(set(edges_tuples))

##Create CFG only to get the leaf nodes.
G = nx.DiGraph()
# G.add_nodes_from(nodes)
G.add_weighted_edges_from(edges_tuples)

leaf_nodes = [v for v, d in G.out_degree() if d == 0]
start_node = [v for v, d in G.in_degree() if d == 0]
updates_edges = append_missing_edges(table_actions, edges, leaf_nodes)

# print "\n\t UPDATED EDGES: ",len(updates_edges)

# 打印 updates_edges
for u in updates_edges:
    print(u)

# 创建带权重的边
G1, weighted_edges = create_cfg(updates_edges)

# 将网络图 G1 写入到 pickle 文件中
with open(file_path + "cfg.pkl", "wb") as f:
    pickle.dump(G1, f)


with open(file_path + "cfg.pkl", "rb") as f:
    data = pickle.load(f)
    print("debug###########",data,"################")

# 打印 weighted_edges
print("\n\t Weighted Edges:")
for i in weighted_edges:
    print(i)




#extract_paths(G1, file_path)

with open(file_path+"weighted_edges.pkl",'wb') as f:
	pickle.dump(weighted_edges, f, protocol=2)

# print "\n\t WEIGHTED EDGES: ",len(weighted_edges)
for we in weighted_edges:
	print(we)

augmenter(p4filename, jsonfile, dotfile, cnt_blk, meta, weighted_edges,file_path)
# nx.draw_shell(G1, with_labels = True, arrows=True)
# plt.show()

################################################
############## TRIED BFS LOGIC #################
################################################

# topological_order = list(nx.topological_sort(G))
# print "\n\t  topological_order: ",len(topological_order),topological_order

# bfs_edge_list = list(nx.bfs_edges(G,topological_order[0]))
# print "\n\t BFS: ",bfs_edge_list

# def identify_next(bfs_edge_list, nodes, comp_node):
# 	for e in bfs_edge_list:
# 		if e[0] == comp_node and e[1] in nodes:
# 			return e[1]
# 		elif e[0] == comp_node and e[1] not in nodes:
# 			identify_next(bfs_edge_list, nodes, e[1])

# for e in edges:
# 	if e['src'] in nodes and e['dst'] not in nodes:
# 		n = identify_next(bfs_edge_list, nodes, e['dst'])
# 		print "\n\t Src Node :", e['src']
# 		print "\n\t Next Node :", n

# nx.draw_shell(G, with_labels = True, arrows=True)
# plt.show()
