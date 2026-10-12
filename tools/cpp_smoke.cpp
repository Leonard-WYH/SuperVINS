#include "extractor_matcher_dpl.h"
#include <limits>
#include <cmath>
#include <iostream>
#include <algorithm>
int main(int argc,char**argv){
 try{
  if(argc!=5)throw std::runtime_error("usage: cpp_smoke superpoint.onnx lightglue.onnx image.png profile_prefix");
  std::cout<<"ORT version "<<OrtGetApiBase()->GetVersionString()<<std::endl;
  Extractor_DPL ex(1);Matcher_DPL ma(1);
  ex.initialize(argv[1],SUPERPOINT);ma.initialize(argv[2],SUPERPOINT,.5f);
  // Recreate sessions with profiling while preserving upstream provider options.
  std::string prefix=argv[4];
  ex.session_options.EnableProfiling((prefix+"_sp").c_str());
  ma.session_options.EnableProfiling((prefix+"_lg").c_str());
  ex.Session=std::make_unique<Ort::Session>(ex.env,argv[1],ex.session_options);
  ma.Session=std::make_unique<Ort::Session>(ma.env,argv[2],ma.session_options);
  cv::Mat a=cv::imread(argv[3],cv::IMREAD_GRAYSCALE),b;
  if(a.empty())throw std::runtime_error("image missing");
  cv::Mat affine=(cv::Mat_<double>(2,3)<<1,0,6,0,1,0);cv::warpAffine(a,b,affine,a.size());
  std::vector<cv::Point2f> k0,k1;std::vector<float>d0,d1;cv::Mat images[2]={a,b};
  for(int i=0;i<2;i++){
   auto im=ex.pre_process(images[i],ex.scale);
   auto t=std::chrono::steady_clock::now();auto r=ex.extract_featurepoints(im);
   auto &k=i?k1:k0;auto &d=i?d1:d0;k=r.first;d.assign(r.second,r.second+k.size()*256);
   if(k.empty()||!std::all_of(d.begin(),d.end(),[](float x){return std::isfinite(x);}))throw std::runtime_error("invalid descriptors");
   for(auto &v:ex.outputtensors[0])if(v.GetTensorTypeAndShapeInfo().GetElementType()==ONNX_TENSOR_ELEMENT_DATA_TYPE_FLOAT){auto n=v.GetTensorTypeAndShapeInfo().GetElementCount();auto p=v.GetTensorData<float>();for(size_t j=0;j<n;j++)if(!std::isfinite(p[j]))throw std::runtime_error("nonfinite SP output");}
   k=ma.pre_process(k,im.rows,im.cols);
   std::cout<<"SP keypoints="<<k.size()<<" desc_dim=256 ms="<<std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-t).count()<<std::endl;
  }
  for(int i=0;i<6;i++){
   auto t=std::chrono::steady_clock::now();auto m=ma.match_featurepoints(k0,k1,d0.data(),d1.data());
   std::cout<<"LG iteration="<<i<<" matches="<<m.size()<<" avg_score="<<ma.last_avg_match_score<<" ms="<<std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-t).count()<<std::endl;
   if(m.empty()||!std::isfinite(ma.last_avg_match_score))throw std::runtime_error("LightGlue failed");
  }
  std::cout<<"PROFILE_SP="<<ex.Session->EndProfilingAllocated(ex.allocator).get()<<std::endl;
  std::cout<<"PROFILE_LG="<<ma.Session->EndProfilingAllocated(ma.allocator).get()<<std::endl;
  std::cout<<"PASS C++ upstream Extractor_DPL/Matcher_DPL"<<std::endl;
 }catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<std::endl;return 1;}
}
