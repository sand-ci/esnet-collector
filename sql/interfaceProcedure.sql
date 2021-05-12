delimiter $$
create procedure insert_or_update( in p_name varchar(128), in time varchar(13))
begin
IF NOT EXISTS (select * from interfaces where name = p_name and status = 1)
THEN
insert into interfaces (name, status, active_from, active_until) values (p_name, 1, time, 1);
ELSE
update interfaces set active_until = 1 where name = p_name and status = 1;
END IF;
end $$
