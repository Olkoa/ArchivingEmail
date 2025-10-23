

import importlib
def topic_build():
    #import dep
    import eml_json
    eml_json.run_email_extraction("Éléments envoyés")
    import bertopicgpu
    import transform_bert
    import split_topic
    import gpt4_1
    import k_medioid
    import k_plot
    import merge
    import data_proc
    import kdist
    import score_plot
    import data_proc2
    import hirrachical_clust
    import cluster_tree
    
if __name__ == "__main__":
    topic_build()