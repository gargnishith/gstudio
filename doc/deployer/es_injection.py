from bson import json_util
import os
import sys
import json
from elasticsearch import Elasticsearch
from gnowsys_ndf.ndf.models import *

#from gnowsys_ndf.settings import GSTUDIO_SITE_NAME
#from gnowsys_ndf.local_settings import GSTUDIO_DOCUMENT_MAPPING
from gnowsys_ndf.local_settings import GSTUDIO_ELASTIC_SEARCH_INDEX

try:
    from bson import ObjectId
except ImportError:  # old pymongo
    from pymongo.objectid import ObjectId
##### use the below commented lines if you are working with Python 2.x   #####
# reload(sys)
# sys.setdefaultencoding('UTF8')

es = Elasticsearch("http://elastic:changeme@gsearch:9200", timeout=100, retry_on_timeout=True)

#author_index = "author_" + GSTUDIO_SITE_NAME.lower()
#index = GSTUDIO_SITE_NAME.lower()
#gsystemtype_index = "node_type_" + GSTUDIO_SITE_NAME.lower()

page_id = 0


def index_docs(all_docs,index,doc_type):
    k = 0
    all_docs_count = all_docs.count()
    for docs in all_docs:
        print "[ %s/%s ] : %s " % (k, all_docs_count, docs._id)


        doc = json.dumps(docs, cls=NodeJSONEncoder)  # convert mongoDB object to a JSON string
        # doc = json.loads(doc,object_hook=json_util.object_hook) ->get back mongoDB object from JSON string

        document = json.loads(doc)  # convert JSON string to a python dictionary
        # doc = json.dumps(document) #convert python dictionary to JSON string
        document["id"] = document.pop("_id")
        document["type"] = document.pop("_type")

        #for docs in doc_type:
        print document["type"]
        #print document

        if document["type"] == "GAttribute":

            es.index(index=index, doc_type="gattribute", id=document["id"], body=document)
            #file_name.write(document["id"] + '\n')

        elif document["type"] == "GRelation":
            es.index(index=index, doc_type="grelation", id=document["id"], body=document)
            #file_name.write(document["id"] + '\n')
        elif document["type"] == "MetaType":
            es.index(index=index, doc_type="metaType", id=document["id"], body=document)
            #file_name.write(document["id"] + '\n')
        elif document["type"] == "GSystemType":
            es.index(index=index, doc_type="gsystemType", id=document["id"], body=document)
            #file_name.write(document["id"] + '\n')
        elif document["type"] == "Author":
            es.index(index=index, doc_type="author", id=document["id"], body=document)
            #file_name.write(document["id"] + '\n')
        elif document["type"] == "RelationType":
            es.index(index=index, doc_type="relationtype", id=document["id"], body=document)
            #file_name.write(document["id"] + '\n')
        elif document["type"] == "AttributeType":
            es.index(index=index, doc_type="attributetype", id=document["id"], body=document)
            #file_name.write(document["id"] + '\n')
        elif document["type"] == "GSystem":
            es.index(index=index, doc_type="gsystem", id=document["id"], body=document)
            #file_name.write(document["id"] + '\n')
            get_doc_type=get_document_type(document)
            #print(get_doc_type)

            es.index(index="gsystem", doc_type=get_doc_type, id=document["id"], body=document)

        elif document["type"] == "Group":
            es.index(index=index, doc_type="group", id=document["id"], body=document)
            #file_name.write(document["id"] + '\n')
        elif document["type"] == "ToReduceDocs":
            es.index(index=index, doc_type="toreducedocs", id=document["id"], body=document)
           # file_name.write(document["id"] + '\n')
        elif document["type"] == "node_holder":
            es.index(index=index, doc_type="node_holder", id=document["id"], body=document)
            #file_name.write(document["id"] + '\n')
        elif document["type"] == "File":
            es.index(index=index, doc_type="file", id=document["id"], body=document)
            #file_name.write(document["id"] + '\n')

        else:
            print index
            # print str(doc_type).strip('[]').replace("'", "").lower()
            es.index(index=index, doc_type=str(doc_type).strip('[]').replace("'", "").lower(), id=document["id"],
                     body=document)
            #file_name.write(document["id"] + '\n')


        k += 1

    #file_name.close()



def get_document_type(document):

	if document["type"]=="GSystem":
		#for ids in document['member_of']:  #document is a member of the Page GSystemType
			#if(ids == page_id):
				#return "Page"
		if('if_file' in document.keys()):
			if(document["if_file"]["mime_type"] is not None):
				data = document["if_file"]["mime_type"].split("/")
				doc_type = data[0]
			else:
				doc_type = "NotMedia"
		else:
			doc_type = "NotMedia"

	else:
		doc_type = "DontCare"
	return doc_type



def main():
    #f = open("/data/nodes.txt", "w")
    #os.chmod("/data/nodes.txt", 0o777)

    nodes = {}
    triples = {}
    benchmarks = {}
    filehives = {}
    buddys = {}
    counters = {}

    #all_docs = [ triples, buddys, benchmarks, nodes, counters]

    print("Starting the indexing process...")

    for index, doc_type in GSTUDIO_ELASTIC_SEARCH_INDEX.items():
        temp = []

        with open("/home/docker/code/gstudio/gnowsys-ndf/gnowsys_ndf/req_body.json") as req_body:
            request_body = json.load(req_body)
        with open("/home/docker/code/gstudio/gnowsys-ndf/gnowsys_ndf/triples.json") as triples:
            triples = json.load(triples)

        if (not es.indices.exists("gsystem")):
            res = es.indices.create(index="gsystem", body=request_body)

        if (not es.indices.exists(index.lower())):
            if (index.lower() == "triples"):
                res = es.indices.create(index=index.lower(), body=triples)
            else:
                res = es.indices.create(index=index.lower(), body=request_body)


        if (es.indices.exists(index.lower())):

            res = es.search(index=index.lower(), body={"query": {"match_all": {}}, "_source": ["id"]}, scroll="1m", size="10")

            scrollid = res['_scroll_id']

            while len(res['hits']['hits']) > 0:

                for hit in res['hits']['hits']:
                    # print(hit["_source"]["id"])
                    # f.write(hit["_source"]["id"] + '\n')
                    # res = es.search(index="nodes", body={"scroll_id": '"' + scrollid + '"'}, search_type="scan",
                    #           scroll="1m", size="10")
                    temp.append(ObjectId(hit["_source"]["id"]))

                res = es.scroll(scrollid, scroll="1m")


            if(index.lower() == "nodes"):
                nodes = node_collection.find({ '_id': {'$nin': temp} }).batch_size(5)

                if(nodes.count() == 0):
                    print("All "+ index.lower() +" documents has injected to elasticsearch")
                    continue
                else:
                    index_docs(nodes, index.lower(), doc_type)

            elif (index.lower() == "triples"):
                triples = triple_collection.find({ '_id': {'$nin': temp} }).batch_size(5)
                if (triples.count() == 0):
                    print("All " + index.lower() + " documents has injected to elasticsearch")
                    continue
                else:
                    # f = open("/data/triples.txt", "w")
                    # os.chmod("/data/triples.txt", 0o777)
                    index_docs(triples, index.lower(), doc_type)

            elif (index.lower() == "filehives"):
                filehive = filehive_collection.find({ '_id': {'$nin': temp} }).batch_size(5)
                if (filehive.count() == 0):
                    print("All " + index.lower() + " documents has injected to elasticsearch")
                    continue
                else:
                    # f = open("/data/triples.txt", "w")
                    # os.chmod("/data/triples.txt", 0o777)
                    index_docs(filehive, index.lower(), doc_type)

            elif (index.lower() == "benchmarks"):
                benchmarks = benchmark_collection.find({ '_id': {'$nin': temp} }).batch_size(5)
                if (benchmarks.count() == 0):
                    print("All " + index.lower() + " documents has injected to elasticsearch")
                    continue
                else:
                    index_docs(benchmarks, index.lower(), doc_type)

            elif (index.lower() == "filehives"):
                filehives = filehive_collection.find({ '_id': {'$nin': temp} }).batch_size(5)
                if (filehives.count() == 0):
                    print("All " + index.lower() + " documents has injected to elasticsearch")
                    continue
                else:
                    index_docs(filehives, index.lower(), doc_type)
                    
            elif (index.lower() == "buddies"):
                buddys = buddy_collection.find({ '_id': {'$nin': temp} }).batch_size(5)
                if (buddys.count() == 0):
                    print("All " + index.lower() + " documents has injected to elasticsearch")
                    continue
                else:
                    index_docs(buddys, index.lower(), doc_type)

            elif (index.lower() == "counters"):
                counters = counter_collection.find({ '_id': {'$nin': temp} }).batch_size(5)
                if (counters.count() == 0):
                    print("All " + index.lower() + " documents has injected to elasticsearch")
                    continue
                else:
                    index_docs(counters, index.lower(), doc_type)


            #print(res['_scroll_id'])
            #print(res['hits']['total'])

                #f = open("/data/nodes.txt", "w+")
                #os.chmod("/data/nodes.txt", 0o777)

                   # f = open("/data/nodes.txt", "w+")
                    # os.chmod("/data/nodes.txt", 0o777)

                    # es.scroll(scrollid, scroll="1m")

                    #print(temp)

                    # DELETING existing/old indexes

                    # for index in GSTUDIO_ELASTIC_SEARCH_INDEX.keys():
                    # if (es.indices.exists(index.lower())):
                    #   print("Deleting the existing index: " + index.lower() + " for reindexing")
                    #   res = es.indices.delete(index=index.lower())
                    #   print("The delete response is %s " % res)


                    # --- END of DELETING existing/old indexes


   
main()