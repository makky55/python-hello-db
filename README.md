# python-hello-db
App Runner + VPC のサンプルコード。
参考blog: https://aws.amazon.com/jp/blogs/news/deep-dive-on-aws-app-runner-vpc-networking/

参考blog から以下を変更しています。
* DB認証をIAMデータベース認証からパスワード認証に変更。
* Auroraのパスワードはパラメータストアに保管し、App Runner からパラメータストアへのアクセスは VPC エンドポイントを利用。
* Aurora は Serverless ではなくProvisionedのクラスタを利用。

# 構成図

<img src="https://user-images.githubusercontent.com/23633944/160276162-7c995533-5554-475e-8b6b-8e6082695268.png" width="800px">

# 手順
## 0. リポジトリのコピー
このリポジトリを自分のアカウントのリポジトリにコピーしてください。

## 1. Amazon Aurora MySQL の準備 
参考blogでは、Aurora Serverless で IAMデータベース認証を利用すると書いてあるが、Aurora Serverless では IAMデータベース認証をサポートしていないので、Provisioned のAurora MySQLを作成します。

* プライベートサブネットにAurora MySQL を作成します。
* 同じ VPC 内で Amazon Linux EC2 インスタンスを起動します。EC2 インスタンスからデータベースに接続するには、MySQL クライアントが必要です。MySQL のコミュニティ開発ブランチである MariaDB をインストールします。
	```
	sudo yum install mariadb
	```
* 管理者ユーザーを使用してデータベースに接続します。
	```
	mysql -h <DATABASE_HOST> -u admin -p
	```
* 管理者ユーザーのパスワードを入力してログインします。次に、IAM 認証を使用するように設定された新しいユーザー (user01) を作成します。
	```
	create user 'user01'@'%' identified by '<パスワード>';
	```
* bookcase データベースを作成し、user01 へ bookcase データベースにクエリを実行する権限を付与します。
	```
	CREATE DATABASE bookcase;
	GRANT SELECT ON bookcase.* TO 'user01'@'%';
	```
* authors テーブルと books テーブルを作成します。
	```
	CREATE TABLE authors (
	  authorId INT,
	  name varchar(255)
 	);
	
	CREATE TABLE books (
	  bookId INT,
	  authorId INT,
	  title varchar(255),
	  year INT
	);
	```
* 2 つのテーブルにいくつかの値を挿入します。
	```
	INSERT INTO authors VALUES (1, "Issac Asimov");
	INSERT INTO authors VALUES (2, "Robert A. Heinlein");
	INSERT INTO books VALUES (1, 1, "Foundation", 1951);
	INSERT INTO books VALUES (2, 1, "Foundation and Empire", 1952);
	INSERT INTO books VALUES (3, 1, "Second Foundation", 1953);
	INSERT INTO books VALUES (4, 2, "Stranger in a Strange Land", 1961);
## 2. Amazon RDS API Endpoint 用 の VPC エンドポイントの作成
参考blogには無い手順ですが、Amazon RDS API Endpoint を使って SSM の API Endpoint に接続します。以下主な注意点です。

* 名前タグを入力し、サービスカテゴリに AWS のサービスを選択します。サービスで "com.amazonaws.ap-northeast-1.ssm"を選択します。
	
	<img src="https://user-images.githubusercontent.com/23633944/160745925-6ad05ea7-6d9c-4cbc-a14e-c842f8103fac.png" width="600px">
	
* Aurora MySQL と同じVPC / プライベートサブネットを選択します。
	<img src="https://user-images.githubusercontent.com/23633944/160746102-9d8be14c-06ea-431b-9285-9f78605f1730.png" width="600px">
* App Runner のタスク からの接続を拒否しないセキュリティグループを選択します。
* エンドポイントが作成済みになったことを確認します。
	<img src="https://user-images.githubusercontent.com/23633944/160746639-5ca6f202-173a-41d8-8749-ace0a124f901.png" width="800px">

## 3. パラメータの作成
* Aurora のパスワード用をパラメータストアを作成します。以下の設定をして、パラメータを作成 をクリックします。
	* 名前: DB_PASS
	* タイプ: 安全な文字列
	* 値: <Aurora の user01 ユーザ のパスワード>
	<img src="https://user-images.githubusercontent.com/23633944/160814818-0db9ed58-507b-45e2-a976-852905ae3183.png" width="600px">
	
## 4. App Runner タスク 用 の IAM ロールの作成
* Get-Parameters という名前の IAM ロールを作成します。このロールには以下のポリシーを付与します。
	```
	{
	    "Version": "2012-10-17",
	    "Statement": [
 	       {
	            "Sid": "VisualEditor0",
	            "Effect": "Allow",
	            "Action": "ssm:GetParameters",
	            "Resource": "*"
	        }
	    ]
	}
	```
	```
	{
	    "Version": "2012-10-17",
	    "Statement": [
	        {
	            "Sid": "VisualEditor0",
	            "Effect": "Allow",
	            "Action": "kms:Decrypt",
	            "Resource": "*"
	        }
	    ]
	}
	```
* IAMロールの信頼ポリシーには、以下の構成を設定します。 
	```
	{
	  "Version": "2012-10-17",
	  "Statement": [
	    {
	      "Effect": "Allow",
	      "Principal": {
	        "Service": "tasks.apprunner.amazonaws.com"
	      },
	      "Action": "sts:AssumeRole"
	    }
	  ]
	}
	```

## 5. App Runner のサービスの作成
* App Runner の画面で サービスの作成 を選択します。
	<img src="https://user-images.githubusercontent.com/23633944/160281340-71a28b00-f716-44b7-bf86-1c0f1fd261f4.png" width="600px">
* ソースコードレポジトリ を選択して、新規追加をクリックします。
	<img src="https://user-images.githubusercontent.com/23633944/160281498-9b075c39-49f4-4b5a-b817-d977b8e032a3.png" width="600px">
* ユーザ名(またはメールアドレス)とパスワードを入力して GitHub にログインします。
	<img src="https://user-images.githubusercontent.com/23633944/160285978-7015fb8f-ffc7-4843-8ecf-333b7261e0b0.png" width="600px">
* Authorize AWS Connector for GitHub をクリックします。
	<img src="https://user-images.githubusercontent.com/23633944/160287283-ebcca49a-e65a-4de3-94f6-f11bb0db108d.png" width="600px">
* 接続名に名前を入力して 別のアプリケーションをインストールする をクリックします。
	<img src="https://user-images.githubusercontent.com/23633944/160808097-a66f2ae8-eec7-4724-93d9-9fb0000af250.png" width="600px">
* Install をクリックします。

	<img src="https://user-images.githubusercontent.com/23633944/160808379-b7bdbd24-8762-48d1-b2ab-1b7618f5baa4.png" width="600px">
* 以下のようにエラーが表示されたら、キャンセルをクリックしてください。

 	<img src="https://user-images.githubusercontent.com/23633944/160822058-ea0a1e90-eda0-47e3-9e96-f8adfbc70c69.png" width="600px">

* 再度新規追加をクリックしてください。

	<img src="https://user-images.githubusercontent.com/23633944/160281498-9b075c39-49f4-4b5a-b817-d977b8e032a3.png" width="600px">

* GitHubアプリケーションにアカウントを選択して、次へをクリックします。

	<img src="https://user-images.githubusercontent.com/23633944/160810751-a958a3c7-bc4d-4bdc-ba6f-f1d7ef89afb9.png" width="600px">


* リポジトリとブランチを選択して、デプロイトリガーに手動を選択し、次へをクリックします。

	<img src="https://user-images.githubusercontent.com/23633944/160811412-7f052512-878a-4587-b4db-b495ded824f8.png" width="600px">

* ランタイム、構築コマンド、開始コマンド、ポートを入力します。
	* ランタイム: python3		
	* 構築コマンド: pip install -r requirements.txt
	* 開始コマンド: python server.py
	* ポート: 8080
	<img src="https://user-images.githubusercontent.com/23633944/160288620-ba0e8d09-af4f-4719-8190-8d3fcf294218.png" width="600px">

* サービス名、仮想CPUとメモリ、環境変数を入力します。
	* サービス名: bookcase
	* 仮想CPUとメモリ: 1vCPU 2GB
	* 環境変数
		* DATABASE_HOST: データベースインスタンスのエンドポイント名
		* DATABASE_NAME: bookcase
		* DATABASE_PASS: DB_PASS
		* DATABASE_PORT: 3306
		* DATABASE_USER: user01
	<img src="https://user-images.githubusercontent.com/23633944/160813643-8f8961cf-f15c-428d-b62e-5b30de22e6dd.png" width="600px">

* 作成したIAM ロールを選択します。
	
	<img src="https://user-images.githubusercontent.com/23633944/160814177-b9c80c4f-309d-4b25-b0c7-a86640d71cc6.png" width="600px">

* カスタム VPC を選択して新規追加をクリックして VPC コネクタを作成します。
	
	<img src="https://user-images.githubusercontent.com/23633944/160289402-2f017b80-1c57-4972-be11-4edf14fe5ee3.png" width="600px">

* VPC コネクタの設定をします。
	* VPC コネクタ名: my-vpc
	* VPC: Aurora MySQL のVPCを選択
	* サブネット: プライベートサブネットを選択
	* セキュリティグループ:  App Runner のタスク からの接続を拒否しないセキュリティグループを選択します。
	
	<img src="https://user-images.githubusercontent.com/23633944/160289840-5af3d414-369f-4c64-b67f-7367518163af.png" width="600px">

* 次へをクリックします。
	
* 作成とデプロイをクリックします。

## 5. デプロイの確認
* Create Service が成功しましたと表示されます。デフォルトドメインをクリックします。

	<img src="https://user-images.githubusercontent.com/23633944/160290704-616b952a-edef-412b-b14d-9b2bfc11771b.png" width="600px">

* 以下のように表示されたら成功です。
	
	<img src="https://user-images.githubusercontent.com/23633944/160290758-4a5648d0-a380-47a7-8c90-af3d370bd504.png" width="600px">
