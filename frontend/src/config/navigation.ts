import type {Page} from '../types';
import {LayoutDashboard, ListChecks, Network, ShieldAlert} from '../icons';
import type {LucideIcon} from 'lucide-react';

export type NavigationItem = {id: Page; label: string; icon: LucideIcon};

/** 사이드바 메뉴와 아이콘을 한 곳에서 관리합니다. */
export const navigationItems: NavigationItem[] = [
  {id:'dashboard', label:'운영 대시보드', icon:LayoutDashboard},
  {id:'runs', label:'실행 이력', icon:ListChecks},
  {id:'api', label:'API 모니터링', icon:Network},
  {id:'incidents', label:'장애·복구 기록', icon:ShieldAlert},
];
