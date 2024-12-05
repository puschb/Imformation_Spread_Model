import pandas as pd
import csv
from collections import deque
import math
class Node:
    def __init__(self, comment_id, parent_comment_id, time_stamp_created, comment_text, user, corresponding_post_id, link):
        self.comment_id = comment_id  
        self.parent_comment_id = parent_comment_id 
        self.parent_node = None
        self.time_stamp_created = time_stamp_created  
        self.comment_text = comment_text  
        self.user = user 
        self.corresponding_post_id = corresponding_post_id 
        self.link = link 
        self.children = []  

    def add_child(self, child_node):
        """Add a child comment to this comment."""
        self.children.append(child_node)

    def get_previous_responses(self):
        cur_node = self.parent_node
        previous_responses = []
        while not cur_node is None:
            previous_responses.insert(0, cur_node)
            cur_node = cur_node.parent_node
        return previous_responses 


    def __repr__(self, level=0):
        ret = "\t" * level + f"User: {self.user} (ID: {self.comment_id})\n"
        for child in self.children:
            ret += child.__repr__(level + 1)
        return ret


class PostTree:
    def __init__(self, path_to_post_data, post_id):
        post_df = pd.read_csv(path_to_post_data,
            quoting=csv.QUOTE_NONNUMERIC,
            escapechar='\\',
            encoding='utf-8')
        post_row = post_df[post_df['post_id'] == post_id].iloc[0].to_dict()
        

        self.post_id = post_id 
        self.title = post_row['title']  
        self.content = post_row['content'] 
        self.timestamp = post_row['timestamp']  
        self.num_comments = post_row['num_comments']  # not accurate
        self.link = post_row['link']  
        self.nodes = {}  
        self.root_comments = []  

    def add_comment(self, comment_id, parent_comment_id, time_stamp_created, comment_text, user, link):
        node = Node(comment_id, parent_comment_id, time_stamp_created, comment_text, user, self.post_id, link)
        self.nodes[comment_id] = node

        if parent_comment_id is None:
            self.root_comments.append(node)
        else:
            parent_node = self.nodes[parent_comment_id]
            node.parent_node = parent_node
            parent_node.add_child(node)
  
    def create_comment_tree(self, path_to_comment_csv):
        comments_df = pd.read_csv(path_to_comment_csv,
                                  quoting=csv.QUOTE_NONNUMERIC,
            escapechar='\\',
            encoding='utf-8'
        )
        df = comments_df[comments_df['corresponding_post_id'] == self.post_id]
        
        root_comments = df[df['parent_comment_id'].isna() | (df['parent_comment_id'] == '')]['comment_id'].tolist()
    
        # Queue for BFS
        queue = deque(root_comments)
        visited = [] 

        while queue:
            current_comment_id = queue.popleft()
            visited.append(current_comment_id)

            children = df[df['parent_comment_id'] == current_comment_id]['comment_id'].tolist()
            queue.extend(children)

        for comment in visited:
            comment_row = df[df['comment_id'] == comment].iloc[0].to_dict()
            if not isinstance(comment_row['parent_comment_id'], str) and math.isnan(comment_row['parent_comment_id']):
                comment_row['parent_comment_id'] = None
            else:
                pass
            self.add_comment(comment, comment_row['parent_comment_id'], comment_row['time_stamp_created'], comment_row['comment_text'],
                             comment_row['user'],comment_row['link'])
    
    def bfs_generator(self):
        queue = deque(self.root_comments)  # Start with root comments
        while queue:
            current_node = queue.popleft()
            yield current_node
            queue.extend(current_node.children)


    def __repr__(self):
        ret = f"Post Title: {self.title}\n"
        ret += f"Content: {self.content}\n"
        ret += f"Number of Comments: {self.num_comments}\n"
        ret += "Comments:\n"
        for root_comment in self.root_comments:
            ret += root_comment.__repr__(1)
        return ret
    
class UserCommentHistories:
    # THE PATH SHOULD BE TO THE UNPRUNED AND CLEANED COMMENTS
    def __init__(self, path_to_comment_csv, post_id):
        
        self.post_id = post_id
        comments_df = pd.read_csv(path_to_comment_csv,
            quoting=csv.QUOTE_NONNUMERIC,
            escapechar='\\',
            encoding='utf-8')
        
        users_with_comments_on_post = comments_df[comments_df['corresponding_post_id'] == self.post_id]['user'].unique()
        user_histories_df = comments_df[
        (comments_df['corresponding_post_id'] != self.post_id) &  
        (comments_df['user'].isin(users_with_comments_on_post))   
        ]

        self.user_histories = user_histories_df.groupby('user')['comment_text'].apply(list).to_dict()

    def get_user_history(self, user):
        return self.user_histories[user]
    
    def __repr__(self):
        return str(self.user_histories)


if __name__ == '__main__':
    import numpy as np  
    post_tree = PostTree('/home/puschb/UVA/CBM/Information_Spread_Model/Data/arcticshift/processed/r_books_posts.csv',
                         '18vuw2v')
    post_tree.create_comment_tree('/home/puschb/UVA/CBM/Information_Spread_Model/Data/arcticshift/cleaned/r_books_comments_cleaned_and_pruned.csv')

    user_histories = UserCommentHistories('/home/puschb/UVA/CBM/Information_Spread_Model/Data/arcticshift/cleaned/r_books_comments_cleaned.csv', '18vuw2v')

    print(post_tree)
    print(user_histories.get_user_history('solaramalgama'))

    list_lengths = [len(lst) for lst in user_histories.user_histories.values()]
    mean_length = np.mean(list_lengths)
    std_length = np.std(list_lengths)
    print(f"Mean length: {mean_length}")
    print(f"Standard deviation: {std_length}")

    node = post_tree.nodes['kfvruop']
    prev_responses = node.get_previous_responses()
    for n in prev_responses:
        print(n)

    for node in post_tree.bfs_generator():
      print(node.comment_id)

