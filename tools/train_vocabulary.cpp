#include "extractor_matcher_dpl.h"
#include "DBoW3.h"
#include <iostream>
#include <fstream>
int main(int argc,char**argv){try{
 if(argc!=4)throw std::runtime_error("train_vocabulary model image_glob output.yml.gz");
 Extractor_DPL ex;ex.initialize(argv[1],SUPERPOINT);
 std::vector<cv::String> paths;cv::glob(argv[2],paths,false);std::vector<cv::Mat> features;
 for(auto&p:paths){cv::Mat im=cv::imread(p,0);if(im.empty())continue;auto input=ex.pre_process(im,ex.scale);auto r=ex.extract_featurepoints(input);if(r.first.size()<20)continue;cv::Mat d(r.first.size(),256,CV_32F,r.second);features.push_back(d.clone());std::cout<<p<<" "<<d.rows<<std::endl;}
 if(features.size()<10)throw std::runtime_error("not enough training frames");
 DBoW3::Vocabulary voc(10,4,DBoW3::TF_IDF,DBoW3::L1_NORM);voc.create(features);voc.save(argv[3]);DBoW3::Vocabulary check(argv[3]);if(check.empty())throw std::runtime_error("empty reloaded vocabulary");
 std::cout<<check<<std::endl<<"PASS trained frames="<<features.size()<<std::endl;
}catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}
