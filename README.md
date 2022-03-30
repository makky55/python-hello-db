# python-hello-db
App Runner + VPC のサンプルコード。
参考: https://aws.amazon.com/jp/blogs/news/deep-dive-on-aws-app-runner-vpc-networking/

構成図
<img src="https://user-images.githubusercontent.com/23633944/160276162-7c995533-5554-475e-8b6b-8e6082695268.png" width="600px">

手順
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
* 管理者ユーザーのパスワードを入力してログインします。次に、IAM 認証を使用するように設定された新しいユーザー (bookuser) を作成します。
	```
	create user 'user01'@'%' identified by '<パスワードを指定してください>';
	```
* bookcase データベースを作成し、bookuser へ bookcase データベースにクエリを実行する権限を付与します。
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
	<img src="https://user-images.githubusercontent.com/23633944/160746639-5ca6f202-173a-41d8-8749-ace0a124f901.png" width="600px">

## 3. App Runner タスク 用 の IAM ロールの作成
* IAMロールには、以下のポリシーを付与します。<ACCOUNT> と <DB_RESOURCE_ID> は環境に合わせて変更してください。
