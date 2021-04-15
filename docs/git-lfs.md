# Git处理大文件

下载git-lfs，解压并执行安装脚本

[Releases · git-lfs/git-lfs](https://github.com/git-lfs/git-lfs/releases/)

对于还没有进行追踪的文件，可以使用以下命令

```bash
# 假设我们有一些psd大文件需要追踪
git lfs track "*.psd"

# 上述命令会生成.gitattributes文件，也要提交该文件
git add .gitattributes

# 将文件commit，推送到远程github仓库
git add file.psd
git commit -m "Add design file"
git push origin main
```

对于已经提交的大文件，可以使用 git lfs migrate 命令。[参考链接](https://github.com/git-lfs/git-lfs/blob/main/docs/man/git-lfs-migrate.1.ronn?utm_source=gitlfs_site&utm_medium=doc_man_migrate_link&utm_campaign=gitlfs)

```bash
# 查看项目中占据容量较大的文件
git lfs migrate info --everything

# Convert all zip files in your main branch
$ git lfs migrate import --include-ref=main --include="*.zip"

# Convert all zip files in every local branch
$ git lfs migrate import --everything --include="*.zip"

# Convert all files over 100K in every local branch
$ git lfs migrate import --everything --above=100Kb
```

将指定文件转换为git-lfs处理时，会对所有的提交历史进行重写，push到远程时需要使用 force-push选项。（谨慎使用，最好在项目设计之初就讲大的二进制文件采用gti-lfs管理）。加入-no-rewrite选项可以避免历史提交的更改。

```bash
$ git lfs migrate import -no-rewrite --everything --include="*.zip"
$ git push --force origin master
```

## Clone

clone项目的时候与普通项目也不太相同

```bash
git lfs clone your_repo
```

也可以使用pull命令

```bash
git lfs pull
```

## 可能遇见的错误

### Github

```bash
Remote "github" does not support the LFS locking API. Consider disabling it with:
  $ git config lfs.https://github.com/BrightXiaoHan/TaskDrivenChatBot.git/info/lfs.locksverify false
Post "https://github.com/BrightXiaoHan/TaskDrivenChatBot.git/info/lfs/locks/verify": dial tcp 192.30.255.112:443: i/o timeout
```

只需要根据提示执行 

```bash
git config lfs.https://github.com/BrightXiaoHan/TaskDrivenChatBot.git/info/lfs.locksverify false
```

命令即可

### Gitlab

gitlab 中受保护的分支如master分支是不能进行force-push的，需要在 Setting/Repository/Protected Branch中将对应分支的保护状态解除，才能进行force-push