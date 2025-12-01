"""
LangChain 통합 테스트 스크립트

각 Phase별로 구현된 LangChain 모듈들이 정상 작동하는지 검증합니다.
"""
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_phase1_imports():
    """Phase 1: 기초 설정 및 구조 - 모듈 임포트 테스트"""
    print("\n" + "="*80)
    print("🧪 Phase 1: 기초 설정 및 구조 테스트")
    print("="*80)
    
    try:
        from utils import run_query, insert_doc, make_table_desc_dict, log_step
        print("✅ utils 모듈 임포트 성공")
        
        # DB 연결 테스트
        result = run_query("SELECT 1 as test")
        assert len(result) > 0
        print("✅ DB 연결 성공")
        
        # 테이블 설명 불러오기
        table_desc = make_table_desc_dict()
        assert len(table_desc) > 0
        print(f"✅ 테이블 설명 로드 성공 ({len(table_desc)}개 테이블)")
        
    except Exception as e:
        print(f"❌ Phase 1 실패: {e}")
        return False
    
    return True


def test_phase2_prompts():
    """Phase 2: 프롬프트 관리 - PromptTemplate 테스트"""
    print("\n" + "="*80)
    print("🧪 Phase 2: 프롬프트 템플릿 테스트")
    print("="*80)
    
    try:
        from prompts.sql_generation_prompt import get_sql_generation_prompt
        
        prompt = get_sql_generation_prompt()
        print(f"✅ 프롬프트 템플릿 로드 성공: {type(prompt).__name__}")
        
        # 프롬프트 변수 확인
        from langchain_core.prompts import ChatPromptTemplate
        assert isinstance(prompt, ChatPromptTemplate)
        print(f"✅ ChatPromptTemplate 인스턴스 확인")
        
    except Exception as e:
        print(f"❌ Phase 2 실패: {e}")
        return False
    
    return True


def test_phase3_llm_config():
    """Phase 3: LLM 래퍼 - ChatOpenAI 설정 테스트"""
    print("\n" + "="*80)
    print("🧪 Phase 3: LangChain LLM 설정 테스트")
    print("="*80)
    
    try:
        from config.llm_config import get_llm
        from langchain_openai import ChatOpenAI
        
        llm = get_llm()
        assert isinstance(llm, ChatOpenAI)
        print(f"✅ ChatOpenAI 인스턴스 생성 성공")
        model_name = getattr(llm, "model_name", getattr(llm, "model", None))
        print(f"   - 모델: {model_name}")
        print(f"   - Temperature: {llm.temperature}")
        
    except Exception as e:
        print(f"❌ Phase 3 실패: {e}")
        return False
    
    return True


def test_phase4_retriever():
    """Phase 4: Retriever - DVDRentalRetriever 테스트"""
    print("\n" + "="*80)
    print("🧪 Phase 4: 벡터 검색 Retriever 테스트")
    print("="*80)
    
    try:
        from retrievers.db_retriever import get_dvdrental_retriever, DVDRentalRetriever
        from langchain_core.retrievers import BaseRetriever
        
        retriever = get_dvdrental_retriever(limit=3)
        assert isinstance(retriever, BaseRetriever)
        print(f"✅ DVDRentalRetriever 생성 성공")
        
        # 간단한 검색 테스트
        docs = retriever.invoke("영화")
        assert len(docs) > 0
        print(f"✅ 벡터 검색 실행 성공 ({len(docs)}개 결과)")
        
        # Document 구조 확인
        doc = docs[0]
        assert hasattr(doc, 'page_content')
        assert hasattr(doc, 'metadata')
        assert 'table_name' in doc.metadata
        print(f"   - 검색 결과: {doc.metadata['table_name']}")
        
    except Exception as e:
        print(f"❌ Phase 4 실패: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def test_phase5_chains():
    """Phase 5: 최종 체인 - Text2SQL RAG 테스트"""
    print("\n" + "="*80)
    print("🧪 Phase 5: 통합 RAG 체인 테스트")
    print("="*80)
    
    try:
        from chains.text_to_sql_chain import create_text_to_sql_chain
        
        chain = create_text_to_sql_chain()
        print(f"✅ Text2SQL RAG 체인 생성 성공")
        
        # 체인 구조 확인
        print(f"   - 체인 타입: {type(chain).__name__}")
        
    except Exception as e:
        print(f"❌ Phase 5 실패: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def run_all_tests():
    """모든 테스트 실행"""
    print("\n")
    print("█" * 80)
    print("🚀 LangChain 통합 검증 테스트 시작")
    print("█" * 80)
    
    results = {
        "Phase 1 (구조 설정)": test_phase1_imports(),
        "Phase 2 (프롬프트)": test_phase2_prompts(),
        "Phase 3 (LLM 설정)": test_phase3_llm_config(),
        "Phase 4 (Retriever)": test_phase4_retriever(),
        "Phase 5 (통합 체인)": test_phase5_chains(),
    }
    
    print("\n" + "="*80)
    print("📊 테스트 결과 요약")
    print("="*80)
    
    for phase_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {phase_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "█" * 80)
    if all_passed:
        print("✅ 모든 테스트 통과! LangChain 통합이 성공적으로 완료되었습니다.")
    else:
        print("❌ 일부 테스트 실패. 위의 오류를 확인하고 수정하세요.")
    print("█" * 80 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
