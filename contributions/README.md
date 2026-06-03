이렇게 하면 돼!

## 1. 프로젝트 가져오기 (딱 한 번만 하면 돼)
터미널에서 아래 명령어를 입력해서 내 프로젝트를 네 컴퓨터로 가져와.
```bash
git clone https://github.com/yeonju7kim/CrossBible.git
cd CrossBible
```

## 2. 코드 최신 상태로 만들기 

작업 시작할 때마다 이거 한 번씩만 해줘! (내 코드가 업데이트되었을 수 있으니까)

Claude에게 이렇게 말해:

"main branch로 가서, 리모트에 있는 최신 코드를 pull 해서 내 로컬이랑 똑같이 맞춰줘."

## 3. 기능 만들기 (새 브랜치 사용!)

Main branch에서 코드를 직접 수정하지 말고, 항상 새로운 branch를 만들어서 작업해줘.

Claude에게 이렇게 말해:

"새 기능 구현하려고 하니까 branch 새로 만들어서 이동해줘. Branch 이름은 적당히 기능을 표현하는 걸로 너가 정해줘. 구현할 기능은 다음과 같아. (설명)"

## 4. 나한테 보내기 (Pull Request)

다 만들었으면, 나한테 검토해달라고 요청(PR)을 보내주면 돼.

Claude에게 이렇게 말해:

"작업한 내용을 origin에 push 하고, 내 main 브랜치로 Pull Request를 생성해줘. 제목은 'feat: [기능 요약]'으로 작성해줘."

---
---
---
## 깃 이해해보고 싶으면

인터넷에 검색해도 많이 나오지만, 아주아주 간단하게 설명하자면...
### 1. add, commit, push, pull 
<img width="696" height="571" alt="image" src="https://github.com/user-attachments/assets/c0e5903d-0ec3-4719-a7ff-919cbf3163d9" />

https://github.com/yeonju7kim/CrossBible 이 주소에 있는 코드를 Remote라고 앞으로 부른다.

내 컴퓨터를 Local이라고 부른다.

Local에서 코드를 수정하고 git add > git commit > git push를 해야 Remote 코드가 바뀐다.

준수가 Remote를 수정하게 되면, 내 local pc의 코드는 여전히 예전 코드로 남아 있게 되고, outdated된다. 따라서 git pull을 해야 새로운 코드로 update가 된다.

### 2. branch
그리고 우리는 코드를 수정할 때, branch를 사용한다. 
<img width="1693" height="579" alt="image" src="https://github.com/user-attachments/assets/0501b3bd-25dd-4f5a-9470-3ebc05760560" />

위 그림에 main branch가 있다. 또 feature-A, feature-A-1, feature-B가 있다.

수정을 할 때는 main branch에서 새로운 branch를 만들어서 수정을 하고, 다시 git add > git commit > git push 해서 새로운 branch를 remote로 올린다.

그리고 pull request(검토 요청)을 하면 된다. 그럼 maintainer가 merge를 한다.

이 그림에서도 알 수 있듯 outdated 된 main branch 코드를 사용해도 git의 시스템으로 잘 merge가 된다. 그래서 여러사람이 동시에 작업이 가능하다!
