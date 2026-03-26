"""
下载 sentence-transformers 模型到本地
"""
import os
import sys

def download_model():
    """下载嵌入模型"""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("❌ 未安装 sentence-transformers")
        print("请运行: pip install sentence-transformers")
        return False

    print("=" * 60)
    print("下载 Sentence Transformers 模型")
    print("=" * 60)
    print()

    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    cache_dir = os.path.join(os.path.dirname(__file__), "models")

    print(f"模型: {model_name}")
    print(f"保存路径: {cache_dir}")
    print()
    print("开始下载... (这可能需要几分钟)")
    print()

    try:
        # 下载模型
        model = SentenceTransformer(model_name, cache_folder=cache_dir)
        print()
        print("✅ 模型下载成功！")
        print()

        # 显示模型信息
        print(f"模型维度: {model.get_sentence_embedding_dimension()}")
        print(f"最大序列长度: {model.max_seq_length}")
        print()

        # 显示模型文件
        print("模型文件:")
        model_path = os.path.join(cache_dir, "sentence-transformers_all-MiniLM-L6-v2")
        if os.path.exists(model_path):
            total_size = 0
            for root, dirs, files in os.walk(model_path):
                for file in files:
                    filepath = os.path.join(root, file)
                    size = os.path.getsize(filepath)
                    total_size += size
                    rel_path = os.path.relpath(filepath, model_path)
                    print(f"  {rel_path}: {size / (1024*1024):.2f} MB")

            print()
            print(f"总大小: {total_size / (1024*1024):.2f} MB")
            print()
            print(f"✅ 模型已保存到: {model_path}")

        # 测试模型
        print()
        print("测试模型...")
        test_sentence = "This is a test sentence."
        embedding = model.encode(test_sentence)
        print(f"测试句子: {test_sentence}")
        print(f"嵌入向量形状: {embedding.shape}")
        print()
        print("✅ 模型测试成功！")

        return True

    except Exception as e:
        print()
        print(f"❌ 下载失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = download_model()
    sys.exit(0 if success else 1)
