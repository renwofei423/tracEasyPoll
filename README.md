tracEasyPoll
============

EasyPoll'fork and make better.

== 说明 ==

本插件根据EasyPoll修改而来：


 1. 添加中文支持。

 2. 更换内网可以使用的js图形显示库。

 3. 使得trac各个应用均可以使用。

 4. 支持饼图、bar图。

 5. 其他bug修正。

----
== 安装说明 ==

 1. 投票插件依赖与数据库，请启用插件时安装 easypoll 表到Trac的数据库：

{{{
CREATE TABLE IF NOT EXISTS `easypoll` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `poll_id` varchar(255) COLLATE utf8_bin NOT NULL,
  `poll_identifier` varchar(255) COLLATE utf8_bin NOT NULL,
  `poll_type` varchar(255) COLLATE utf8_bin NOT NULL DEFAULT 'single',
  `poll_title` varchar(255) COLLATE utf8_bin NOT NULL,
  `poll_options` text COLLATE utf8_bin NOT NULL,
  `poll_votes` text COLLATE utf8_bin NOT NULL,
  `poll_creator` varchar(255) COLLATE utf8_bin NOT NULL,
  `last_updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `poll_id` (`poll_id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8 COLLATE=utf8_bin AUTO_INCREMENT=3 ;
}}}

 1. EASYPOLL_CREATE : 用户有权限可以创建投票。（TRAC_ADMIN亦可），请分配对应权限。

 2. EASYPOLL_VOTE : 用户有权限投票。（TRAC_ADMIN亦可），请分配对应权限。

== 使用说明 ==

=== 例子 ===

[[EasyPoll(name=m2yfirstpoll,title=你最爱的水果是?,response_type=multiple,options=苹果:香蕉:橘子:草莓,user_can_change_vote=true,chart_type=bar)]] [[EasyPoll(name=m2yfirstpoll,title=你最爱的水果是?,response_type=multiple,options=苹果:香蕉:橘子:草莓,user_can_change_vote=true,chart_type=bar)]]

投票选项也可以是ticket:

[[EasyPoll(name=m32yfirstpoll,title=最需要解决的ticket?,response_type=multiple,options=#2392:#2389:#2391,user_can_change_vote=true,chart_type=pie)]] [[EasyPoll(name=m32yfirstpoll,title=最需要解决的ticket?,response_type=multiple,options=#2392:#2389:#2391,user_can_change_vote=true,chart_type=pie)]]

=== 选项说明 ===

 1. name(必须):名字是投票的唯一标识，并不会显示这个名称。如果你修改这个名字，会创建新的投票。如果使用相同的名称，会使用相同的投票。建议不要创建投票之后修改此名称。

{{{#!div style="color:red"  请保证'''名字、选项''' 在各个地方的一致性！不一致的选项会导致投票不可用！ }}} {{{#!div style="color:blue"  建议命名规范为：部门+创建者+时间，如: kylinlinux_wz_201206121647。保证名字的唯一性，最好使用英文、数字和符号。 }}}

 1. title(required) : 投票的标题。可以修改。修改之后投票显示会更新。

 2. options(required) : 投票的选项。选项通过 : 号隔开。支持引用trac的任务单(Ticket),比如 option=#2392:#2389:#2391, 投票插件会自动显示任务单(Ticket)的文本信息和链接。

 3. response(optional) : 投票类型，单选或多选（single/multiple）。默认单选。

 4. user_can_change_vote(optional) : 是否可以修改自己的投票结果（true/false）。默认不可以修改(false)。

 5. chart_type(optional) : 图形显示方式，饼图或者条型图(pei/bar)。默认饼图(pie)。

  所有用户能看到投票，但是只有对应权限才能投、或者创建投票。

== 其他注意 ==

 1. 注意使用英文的 ,号来分割不同的选项。选项之间不要空格。